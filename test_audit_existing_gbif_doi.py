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
    "coordinateUncertaintyInMeters\tgbifID\trecordedBy\n"
)
ROW = (
    "2024\t3cba69c8-e24e-4229-8727-cfba163336fb\tCC0_1_0\t"
    "HUMAN_OBSERVATION\tKR\ttrue\tfalse\t36.5\t127.4\t\t"
    "synthetic-not-real-id\tSynthetic Person\n"
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
