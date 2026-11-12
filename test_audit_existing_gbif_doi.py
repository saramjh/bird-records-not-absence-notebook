"""Synthetic-only tests for the read-only GBIF archive audit."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from audit_existing_gbif_doi import audit_archive

HEADER = (
    "year\tdatasetKey\tlicense\tbasisOfRecord\tcountryCode\thasCoordinate\t"
    "hasGeospatialIssues\tdecimalLatitude\tdecimalLongitude\t"
    "coordinateUncertaintyInMeters\tgbifID\toccurrenceStatus\trecordedBy\n"
)
ROW = (
    "2024\t3cba69c8-e24e-4229-8727-cfba163336fb\tCC0_1_0\t"
    "HUMAN_OBSERVATION\tKR\ttrue\tfalse\t36.5\t127.4\t\t"
    "synthetic-not-real-id\tDETECTED\tSynthetic Person\n"
)


class ExistingDOIAuditTests(unittest.TestCase):
    def make_zip(self, folder, *, rights="http://creativecommons.org/publicdomain/zero/1.0/legalcode",
                 citation="https://doi.org/10.15468/ya2fjz", rows=ROW):
        path = Path(folder) / "synthetic.zip"
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("rights.txt", rights)
            archive.writestr("citations.txt", citation)
            archive.writestr("occurrence.txt", HEADER + rows)
        return path

    def test_aggregate_has_no_record_level_fields_or_values(self):
        with TemporaryDirectory() as temp:
            result = audit_archive(self.make_zip(temp), expected_sha256=None,
                                   exact_cohort=False)
        text = json.dumps(result)
        self.assertEqual(result["source_record_count"], 1)
        self.assertEqual(result["year_2024_missing_reported_coordinate_uncertainty"], 1)
        self.assertEqual(result["strict_uncertainty_threshold_usable_records"], 0)
        for forbidden in ("decimalLatitude", "decimalLongitude", "gbifID",
                          "recordedBy", "synthetic-not-real-id", "Synthetic Person"):
            self.assertNotIn(forbidden, text)

    @staticmethod
    def make_record(uncertainty, *, latitude="36.5", longitude="127.4",
                    record_id="synthetic-not-real-id", issues="false", status="DETECTED"):
        row = ROW.replace(
            "\t36.5\t127.4\t\t",
            f"\t{latitude}\t{longitude}\t{uncertainty}\t",
        ).replace("synthetic-not-real-id", record_id)
        return row.replace("\ttrue\tfalse\t", f"\ttrue\t{issues}\t").replace(
            "\tDETECTED\t", f"\t{status}\t")

    def test_strict_threshold_accepts_1000_not_1000_point_1(self):
        rows = (self.make_record("1000", record_id="one") +
                self.make_record("1000.1", record_id="two"))
        with TemporaryDirectory() as temp:
            result = audit_archive(self.make_zip(temp, rows=rows),
                                   expected_sha256=None, exact_cohort=False)
        self.assertEqual(result["year_2024_with_reported_coordinate_uncertainty"], 2)
        self.assertEqual(result["strict_uncertainty_threshold_usable_records"], 1)

    def test_strict_threshold_rejects_invalid_uncertainty(self):
        rows = "".join(self.make_record(value, record_id=str(i))
                       for i, value in enumerate(("-1", "nan", "inf", "invalid", "1001")))
        with TemporaryDirectory() as temp:
            result = audit_archive(self.make_zip(temp, rows=rows),
                                   expected_sha256=None, exact_cohort=False)
        self.assertEqual(result["year_2024_with_reported_coordinate_uncertainty"], 5)
        self.assertEqual(result["strict_uncertainty_threshold_usable_records"], 0)

    def test_strict_threshold_requires_valid_coordinates(self):
        rows = (self.make_record("300", record_id="a", latitude="nan") +
                self.make_record("300", record_id="b", latitude="91") +
                self.make_record("300", record_id="c", longitude="-181") +
                self.make_record("300", record_id="d", latitude="not-coordinate") +
                self.make_record("300", record_id="e"))
        with TemporaryDirectory() as temp:
            result = audit_archive(self.make_zip(temp, rows=rows),
                                   expected_sha256=None, exact_cohort=False)
        self.assertEqual(result["strict_uncertainty_threshold_usable_records"], 1)

    def test_strict_threshold_rejects_duplicate_and_missing_ids(self):
        rows = (self.make_record("300", record_id="same") +
                self.make_record("300", record_id="same") +
                self.make_record("300", record_id=""))
        with TemporaryDirectory() as temp:
            result = audit_archive(self.make_zip(temp, rows=rows),
                                   expected_sha256=None, exact_cohort=False)
        self.assertEqual(result["strict_uncertainty_threshold_usable_records"], 1)

    def test_strict_threshold_rejects_geospatial_issue(self):
        rows = (self.make_record("300", record_id="bad", issues="true") +
                self.make_record("300", record_id="ok", issues="false"))
        with TemporaryDirectory() as temp:
            result = audit_archive(self.make_zip(temp, rows=rows),
                                   expected_sha256=None, exact_cohort=False)
        self.assertEqual(result["strict_uncertainty_threshold_usable_records"], 1)

    def test_strict_threshold_excludes_not_detected_and_unknown_status(self):
        rows = "".join([
            self.make_record("300", record_id="positive", status="DETECTED"),
            self.make_record("300", record_id="legacy", status="PRESENT"),
            self.make_record("300", record_id="nondetection", status="NOT_DETECTED"),
            self.make_record("300", record_id="absent", status="ABSENT"),
            self.make_record("300", record_id="unclassified", status=""),
        ])
        with TemporaryDirectory() as temp:
            result = audit_archive(self.make_zip(temp, rows=rows),
                                   expected_sha256=None, exact_cohort=False)
        self.assertEqual(result["year_2024_records"], 5)
        self.assertEqual(result["year_2024_excluded_non_detection_or_unknown_status"], 3)
        self.assertEqual(result["strict_uncertainty_threshold_usable_records"], 2)

    def test_reject_archive_missing_occurrence_status_field(self):
        with TemporaryDirectory() as temp:
            p = Path(temp) / "missing-status.zip"
            with ZipFile(p, "w", ZIP_DEFLATED) as archive:
                archive.writestr("rights.txt", "http://creativecommons.org/publicdomain/zero/1.0/legalcode")
                archive.writestr("citations.txt", "https://doi.org/10.15468/ya2fjz")
                archive.writestr("occurrence.txt", HEADER.replace("occurrenceStatus\t", "") +
                                 ROW.replace("DETECTED\t", ""))
            with self.assertRaisesRegex(ValueError, "required DwC fields missing"):
                audit_archive(p, expected_sha256=None, exact_cohort=False)

    def test_reject_checksum_change(self):
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                audit_archive(self.make_zip(temp), expected_sha256="0" * 64)

    def test_reject_non_cc0_source_rights(self):
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "not CC0"):
                audit_archive(self.make_zip(temp, rights="CC BY-NC"),
                              expected_sha256=None, exact_cohort=False)

    def test_reject_source_citation_mismatch(self):
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "citation missing"):
                audit_archive(self.make_zip(temp, citation="missing"),
                              expected_sha256=None, exact_cohort=False)

    def test_reject_record_licence_drift(self):
        with TemporaryDirectory() as temp:
            changed = ROW.replace("CC0_1_0", "CC_BY_NC_4_0")
            with self.assertRaisesRegex(ValueError, "licence drift"):
                audit_archive(self.make_zip(temp, rows=changed),
                              expected_sha256=None, exact_cohort=False)


if __name__ == "__main__":
    unittest.main()
