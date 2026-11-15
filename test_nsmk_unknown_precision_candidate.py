"""Synthetic-only tests: missing coordinate precision is never treated as precise."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from nsmk_unknown_precision_candidate import build_unknown_precision_candidate

KEY = "3cba69c8-e24e-4229-8727-cfba163336fb"
META = {
    "key": "0015299-260903145123482",
    "doi": "10.15468/dl.u7tcq5",
    "status": "SUCCEEDED",
    "license": "http://creativecommons.org/publicdomain/zero/1.0/legalcode",
    "request": {
        "predicate": {"type": "equals", "key": "DATASET_KEY", "value": KEY},
        "format": "DWCA",
        "type": "OCCURRENCE",
    },
}
HEADER = (
    "year\tdatasetKey\tlicense\tbasisOfRecord\tcountryCode\thasCoordinate\t"
    "hasGeospatialIssues\tdecimalLatitude\tdecimalLongitude\t"
    "coordinateUncertaintyInMeters\tgbifID\toccurrenceStatus\trecordedBy\n"
)


def row(id_, *, year="2024", status="PRESENT", lat="37.5", lon="127.0",
        uncertainty="", license_="CC0_1_0", dataset=KEY):
    return "\t".join([
        year, dataset, license_, "HUMAN_OBSERVATION", "KR", "true", "false",
        lat, lon, uncertainty, id_, status, "Synthetic Example",
    ]) + "\n"


def make_zip(directory, rows, *, rights="http://creativecommons.org/publicdomain/zero/1.0/legalcode"):
    target = Path(directory) / "synthetic.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        archive.writestr("occurrence.txt", HEADER + rows)
        archive.writestr("rights.txt", rights)
        archive.writestr("citations.txt", "https://doi.org/10.15468/ya2fjz")
    metadata = dict(META, size=target.stat().st_size,
                    totalRecords=len([line for line in rows.splitlines() if line]))
    return target, metadata


def projection(lon, lat):
    # Pure test projector; no real coordinates leave the fixture.
    return float(lon) * 1000, float(lat) * 1000


class UnreportedPrecisionTests(unittest.TestCase):
    def test_aggregate_only_reports_unknown_uncertainty_explicitly(self):
        with TemporaryDirectory() as d:
            target, metadata = make_zip(d, row("synthetic-alpha", lon="127") +
                                            row("synthetic-beta", lon="128") +
                                            row("synthetic-gamma", lon="129"))
            candidate = build_unknown_precision_candidate(
                target, metadata, projection, expected_sha256=None,
                exact_cohort=False)
        self.assertEqual(candidate["accepted_count"], 3)
        self.assertEqual(candidate["unreported_coordinate_uncertainty_count"], 3)
        self.assertEqual(sum(n for _, _, n in candidate["grid_10km"]), 3)
        self.assertEqual(sum(n for _, _, n in candidate["grid_50km"]), 3)
        self.assertFalse(candidate["coordinates_are_verified_to_grid_resolution"])
        self.assertEqual(candidate["status"], "PRIVATE_AUTHOR_REVIEW_ONLY")
        serialized = json.dumps(candidate)
        for banned in ("synthetic-alpha", "synthetic-beta", "Synthetic Example",
                       "decimalLatitude", "recordedBy", "gbifID"):
            self.assertNotIn(banned, serialized)

    def test_missing_precision_is_not_zero_or_1000m(self):
        with TemporaryDirectory() as d:
            target, metadata = make_zip(d, row("a", uncertainty="500"))
            with self.assertRaisesRegex(ValueError, "UNREPORTED_PRECISION_EXPECTED"):
                build_unknown_precision_candidate(target, metadata, projection,
                                                  expected_sha256=None,
                                                  exact_cohort=False)

    def test_explicit_absence_or_unknown_status_excluded(self):
        with TemporaryDirectory() as d:
            target, metadata = make_zip(d, row("yes") +
                                             row("no", status="NOT_DETECTED") +
                                             row("legacy-no", status="ABSENT") +
                                             row("unknown", status=""))
            result = build_unknown_precision_candidate(
                target, metadata, projection, expected_sha256=None,
                exact_cohort=False)
        self.assertEqual(result["accepted_count"], 1)
        self.assertEqual(result["excluded_non_detection_or_unknown_status"], 3)

    def test_duplicate_or_missing_id_hard_fails(self):
        for rows in (row("repeat") + row("repeat"), row("")):
            with self.subTest(rows=rows), TemporaryDirectory() as d:
                target, metadata = make_zip(d, rows)
                with self.assertRaisesRegex(ValueError, "MISSING_OR_DUPLICATE_GBIF_ID"):
                    build_unknown_precision_candidate(target, metadata, projection,
                                                      expected_sha256=None,
                                                      exact_cohort=False)

    def test_invalid_original_coordinate_never_mapped(self):
        for lat, lon in (("nan", "127"), ("91", "127"), ("35", "-181"),
                         ("not-lat", "127")):
            with self.subTest(lat=lat, lon=lon), TemporaryDirectory() as d:
                target, metadata = make_zip(d, row("bad", lat=lat, lon=lon))
                with self.assertRaisesRegex(ValueError, "SOURCE_COORDINATE_INVALID"):
                    build_unknown_precision_candidate(target, metadata, projection,
                                                      expected_sha256=None,
                                                      exact_cohort=False)

    def test_wrong_source_license_or_dataset_rejected(self):
        for records, rights in (
            (row("a", license_="CC_BY_NC_4_0"),
             "http://creativecommons.org/publicdomain/zero/1.0/legalcode"),
            (row("a", dataset="other-data"),
             "http://creativecommons.org/publicdomain/zero/1.0/legalcode"),
            (row("a"), "CC BY-NC"),
        ):
            with TemporaryDirectory() as d:
                target, metadata = make_zip(d, records, rights=rights)
                with self.assertRaises(ValueError):
                    build_unknown_precision_candidate(target, metadata, projection,
                                                      expected_sha256=None,
                                                      exact_cohort=False)

    def test_wrong_download_metadata_rejected(self):
        with TemporaryDirectory() as d:
            target, metadata = make_zip(d, row("a"))
            for key, value in (("doi", "10.15468/dl.other"),
                               ("status", "RUNNING"), ("totalRecords", 2),
                               ("size", 1)):
                with self.subTest(key=key):
                    changed = dict(metadata, **{key: value})
                    with self.assertRaises(ValueError):
                        build_unknown_precision_candidate(
                            target, changed, projection, expected_sha256=None,
                            exact_cohort=False)

    def test_expected_sha256_is_required_in_production_and_must_match(self):
        with TemporaryDirectory() as d:
            target, metadata = make_zip(d, row("a"))
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                build_unknown_precision_candidate(
                    target, metadata, projection, expected_sha256="0" * 64,
                    exact_cohort=False)
            with self.assertRaisesRegex(ValueError, "PRODUCTION_ARCHIVE_SHA_REQUIRED"):
                build_unknown_precision_candidate(
                    target, metadata, projection, expected_sha256=None,
                    exact_cohort=True)

    def test_empty_qualifying_year_rejected(self):
        with TemporaryDirectory() as d:
            target, metadata = make_zip(d, row("historic", year="2023"))
            with self.assertRaisesRegex(ValueError, "NO_ELIGIBLE_2024_RECORDS"):
                build_unknown_precision_candidate(target, metadata, projection,
                                                  expected_sha256=None,
                                                  exact_cohort=False)


if __name__ == "__main__":
    unittest.main()
