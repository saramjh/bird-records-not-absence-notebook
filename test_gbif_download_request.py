"""Offline/no-send regression checks for a future GBIF occurrence-download request."""
import copy
import unittest
from pathlib import Path

from gbif_download_request import BACKBONE, expected_predicate, build_request, read_snapshot

SOURCE = Path(__file__).parent / "data" / "first-page-grids-20261026.json"

class GBIFDownloadRequestTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = read_snapshot(SOURCE)

    def test_exact_full_filter_with_backbone_taxonomy(self):
        manifest = build_request(self.snapshot, "test@example.org")
        self.assertEqual(manifest["format"], "DWCA")
        self.assertEqual(manifest["checklistKey"], BACKBONE)
        self.assertEqual(manifest["notificationAddresses"], ["test@example.org"])
        self.assertEqual(manifest["predicate"], expected_predicate())
        self.assertNotIn("downloadDOI", manifest)
        self.assertNotIn("limit", manifest)
        self.assertEqual(len(manifest["predicate"]["predicates"]), 7)

    def test_gbif_backbone_key_pinned_in_taxon_filter(self):
        p = build_request(self.snapshot, "test@example.org")["predicate"]["predicates"]
        matched = [v for v in p if v.get("key") == "TAXON_KEY"]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["value"], "212")
        self.assertEqual(matched[0]["checklistKey"], BACKBONE)

    def test_never_confuses_existing_download_doi_with_new_query(self):
        altered = copy.deepcopy(self.snapshot)
        altered["GBIF_occurrence_download_doi"] = "10.15468/dl.sp8k2g"
        with self.assertRaises(ValueError):
            build_request(altered, "test@example.org")

    def test_source_selection_drift_fails_closed(self):
        for changed in ["year=2023", "taxonKey=V2", "license=CC_BY_4_0", "country=US"]:
            altered = copy.deepcopy(self.snapshot)
            key = changed.split("=")[0]
            old = {"year":"year=2024", "taxonKey":"taxonKey=212", "license":"license=CC0_1_0", "country":"country=KR"}[key]
            altered["original_api_query"] = altered["original_api_query"].replace(old, changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                build_request(altered, "test@example.org")

    def test_email_validation_and_no_secrets_in_manifest(self):
        for email in ["", "not-an-address", "bad\nHeader: evil@example.org"]:
            with self.subTest(email=email), self.assertRaises(ValueError):
                build_request(self.snapshot, email)
        payload = build_request(self.snapshot, "reader@example.org")
        self.assertNotIn("password", str(payload).lower())
        self.assertNotIn("username", str(payload).lower())

if __name__ == "__main__":
    unittest.main()
