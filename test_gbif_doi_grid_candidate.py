"""Synthetic fixtures for the future GBIF DOI archive-to-grid path."""
import csv
from hashlib import sha256
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from zipfile import ZIP_DEFLATED, ZipFile

from gbif_download_request import BACKBONE, build_request, read_snapshot
from gbif_doi_grid_candidate import audit_download_to_candidate, MAX_UNCOMPRESSED_BYTES

DOI = "10.15468/dl.test7"
KEY = "0015299-260903145123482"
FIELDS = [
    "gbifID", "countryCode", "basisOfRecord", "year", "license",
    "occurrenceStatus", "decimalLatitude", "decimalLongitude",
    "coordinateUncertaintyInMeters", "datasetKey", "hasCoordinate",
    "hasGeospatialIssues", "classKey", "class",
]


def fixture_records():
    def row(id_, status="PRESENT", unc="200", lat="36", lon="127"):
        return dict(gbifID=id_, countryCode="KR", basisOfRecord="HUMAN_OBSERVATION",
                    year="2024", license="CC0_1_0", occurrenceStatus=status,
                    decimalLatitude=lat, decimalLongitude=lon,
                    coordinateUncertaintyInMeters=unc, datasetKey="synthetic-provider",
                    hasCoordinate="true", hasGeospatialIssues="false",
                    classKey="212", **{"class": "Aves"})
    return [
        row("synthetic-1"),
        row("synthetic-2", lat="37", lon="128"),
        row("synthetic-3", status="NOT_DETECTED"),
        row("synthetic-4", unc=""),
        row("synthetic-1"),
        row("synthetic-5", lon="999"),
    ]


def archived_tsv(rows, fields=FIELDS):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, delimiter="\t", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


class ArchiveCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = read_snapshot(Path(__file__).parent /
                                     "data/first-page-grids-20261026.json")

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.archive = Path(self.tmp.name) / "original.zip"
        self.rows = fixture_records()
        self.metadata = {
            "doi": DOI, "key": KEY, "status": "SUCCEEDED",
            "license": "http://creativecommons.org/publicdomain/zero/1.0/legalcode",
            "size": 1024, "totalRecords": len(self.rows),
            "downloadLink": ("https://api.gbif.org/v1/occurrence/download/request/" +
                             KEY + ".zip"),
            "request": {
                "format": "DWCA", "checklistKey": BACKBONE,
                "predicate": build_request(
                    self.snapshot, "synthetic@example.invalid")["predicate"]
            },
        }

    def _zip(self, rows=None, fields=FIELDS, rights=None, citations=None):
        data = archived_tsv(rows if rows is not None else self.rows, fields)
        with ZipFile(self.archive, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("occurrence.txt", data)
            archive.writestr("rights.txt", rights if rights is not None else
                             "http://creativecommons.org/publicdomain/zero/1.0/legalcode")
            archive.writestr("citations.txt", citations if citations is not None else
                             "Dataset: https://doi.org/10.15468/testdoi")
        self.metadata["size"] = self.archive.stat().st_size
        return sha256(self.archive.read_bytes()).hexdigest()

    def _check(self, sha, projector=None):
        return audit_download_to_candidate(
            self.archive, self.metadata, self.snapshot, DOI, sha,
            projector or (lambda lon, lat: (lon * 1000, lat * 1000)))

    def test_aggregated_only_output_and_conservation(self):
        actual = self._check(self._zip())
        self.assertEqual(actual["source_records"], 6)
        self.assertEqual(actual["accepted_count"], 2)
        self.assertEqual(sum(actual["excluded"].values()), 4)
        self.assertEqual(actual["excluded"]["not_detected"], 1)
        self.assertEqual(actual["excluded"]["missing_or_duplicate_id"], 1)
        self.assertEqual(actual["excluded"]["uncertainty_missing"], 1)
        self.assertEqual(actual["excluded"]["invalid_coordinate"], 1)
        self.assertEqual(sum(r[2] for r in actual["grid_10km"]), 2)
        self.assertEqual(sum(r[2] for r in actual["grid_50km"]), 2)
        self.assertFalse(actual["individual_records_redistributed"])
        self.assertFalse(actual["editorial_and_binder_review_complete"])
        self.assertNotIn("synthetic-1", str(actual))
        self.assertNotIn("decimalLatitude", str(actual))

    def test_original_sha_is_mandatory_and_never_guessed(self):
        self._zip()
        for wrong in ("", "missing", "a" * 64):
            with self.subTest(sha=wrong), self.assertRaisesRegex(
                ValueError, "SHA256"):
                self._check(wrong)

    def test_reject_oversized_member_before_decompression(self):
        original_sha = self._zip()
        fake_zip = MagicMock()
        fake_zip.__enter__.return_value = fake_zip
        fake_zip.infolist.return_value = [
            SimpleNamespace(filename="occurrence.txt",
                            file_size=MAX_UNCOMPRESSED_BYTES + 1)
        ]
        fake_zip.testzip.side_effect = AssertionError(
            "testzip should not decompress an oversized archive")
        with patch("gbif_doi_grid_candidate.ZipFile", return_value=fake_zip):
            with self.assertRaisesRegex(ValueError, "ARCHIVE_TOO_LARGE_FOR_REVIEW"):
                self._check(original_sha)
        fake_zip.testzip.assert_not_called()

    def test_reject_download_metadata_size_mismatch(self):
        expected = self._zip()
        self.metadata["size"] += 1
        with self.assertRaisesRegex(ValueError, "ARCHIVE_SIZE_DIFFERS"):
            self._check(expected)

    def test_reject_missing_status_column(self):
        f = [x for x in FIELDS if x != "occurrenceStatus"]
        with self.assertRaisesRegex(ValueError, "REQUIRED_OCCURRENCE_FIELDS"):
            self._check(self._zip(fields=f))

    def test_reject_non_cc0_or_out_of_scope_record(self):
        for k,v in [("license","CC_BY_4_0"),("year","2023"),
                    ("countryCode","US"),("hasGeospatialIssues","true"),
                    ("basisOfRecord","PRESERVED_SPECIMEN")]:
            rows=fixture_records()
            rows[1][k]=v
            with self.subTest(field=k), self.assertRaisesRegex(
                ValueError, "OUTSIDE_VERIFIED_DOWNLOAD_SELECTION"):
                self._check(self._zip(rows=rows))

    def test_reject_wrong_taxonomic_class(self):
        for k,v in [("classKey","999"),("class","Mammalia")]:
            rows=fixture_records()
            rows[0][k]=v
            with self.subTest(field=k), self.assertRaisesRegex(
                ValueError,"NON_AVES_CLASS"):
                self._check(self._zip(rows=rows))

    def test_reject_missing_provider_citation_or_rights(self):
        with self.assertRaisesRegex(ValueError, "RIGHTS_OR_CITATIONS"):
            self._check(self._zip(rights="All rights reserved"))
        with self.assertRaisesRegex(ValueError, "RIGHTS_OR_CITATIONS"):
            self._check(self._zip(citations="missing DOI provenance"))

    def test_reject_archive_row_count_drift(self):
        self.metadata["totalRecords"] += 1
        with self.assertRaisesRegex(ValueError,"ROW_COUNT_MISMATCH"):
            self._check(self._zip())

    def test_reject_download_metadata_filter_drift(self):
        meta=self.metadata["request"]["predicate"]["predicates"]
        next(x for x in meta if x["key"]=="COUNTRY")["value"]="US"
        with self.assertRaisesRegex(ValueError,"FILTERS_DIFFER"):
            self._check(self._zip())

    def test_reject_malformed_projected_coordinates(self):
        with self.assertRaisesRegex(ValueError,"INVALID_PROJECTED"):
            self._check(self._zip(), projector=lambda lon,lat: (float("nan"),10))

    def test_reject_no_qualified_records(self):
        rows=fixture_records()
        for row in rows:
            row["coordinateUncertaintyInMeters"]=""
        with self.assertRaisesRegex(ValueError,"NO_QUALIFIED_RECORDS"):
            self._check(self._zip(rows=rows))


if __name__ == "__main__":
    unittest.main()
