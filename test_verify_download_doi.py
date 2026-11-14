"""Synthetic-only tests. Never submit a GBIF request or store occurrence rows."""
import copy
import unittest
from pathlib import Path

from gbif_download_request import BACKBONE, read_snapshot, build_request
from verify_download_doi import validate_download_metadata

SNAPSHOT = Path(__file__).parent / "data" / "first-page-grids-20261026.json"
DOI = "10.15468/dl.test7"


def good_metadata(snapshot):
    return {
        "key": "0015299-260903145123482",
        "doi": DOI,
        "status": "SUCCEEDED",
        "license": "http://creativecommons.org/publicdomain/zero/1.0/legalcode",
        "size": 123456,
        "totalRecords": 5519,
        "downloadLink": "https://api.gbif.org/v1/occurrence/download/request/0015299-260903145123482.zip",
        "request": {
            "format": "DWCA",
            "checklistKey": BACKBONE,
            "predicate": copy.deepcopy(build_request(snapshot, "unit-test@example.org")["predicate"]),
        },
    }


class DOIReadOnlyMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = read_snapshot(SNAPSHOT)

    def test_exact_full_selection_passes(self):
        result = validate_download_metadata(good_metadata(self.snapshot), self.snapshot, DOI)
        self.assertTrue(result["exact_full_query_metadata_match"])
        self.assertFalse(result["archive_sha256_verified"])
        self.assertFalse(result["archive_contents_audited"])
        self.assertTrue(result["no_download_or_provider_write"])
        self.assertTrue(result["not_the_historical_first_100_sample"])
        self.assertNotIn("coordinates", str(result).lower())

    def test_permutation_and_default_match_case_are_harmless(self):
        meta = good_metadata(self.snapshot)
        children = meta["request"]["predicate"]["predicates"]
        children.reverse()
        for child in children:
            child["matchCase"] = False
        self.assertTrue(validate_download_metadata(meta, self.snapshot, DOI)["exact_full_query_metadata_match"])

    def test_any_filter_change_fails_closed(self):
        for key, value in [
            ("YEAR", "2023"),
            ("TAXON_KEY", "123"),
            ("COUNTRY", "US"),
            ("BASIS_OF_RECORD", "PRESERVED_SPECIMEN"),
            ("LICENSE", "CC_BY_4_0"),
            ("HAS_COORDINATE", "false"),
            ("HAS_GEOSPATIAL_ISSUE", "true"),
        ]:
            m = good_metadata(self.snapshot)
            filt = next(x for x in m["request"]["predicate"]["predicates"] if x["key"] == key)
            filt["value"] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "FILTERS"):
                validate_download_metadata(m, self.snapshot, DOI)

    def test_extra_or_missing_filter_fails(self):
        for operation in ("remove", "append", "duplicate"):
            m = good_metadata(self.snapshot)
            children = m["request"]["predicate"]["predicates"]
            if operation == "remove":
                children.pop()
            elif operation == "append":
                children.append({"type":"equals", "key":"DATASET_KEY", "value":"any"})
            else:
                children[-1] = copy.deepcopy(children[0])
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                validate_download_metadata(m, self.snapshot, DOI)

    def test_old_koreaves_dataset_only_download_is_rejected(self):
        m = good_metadata(self.snapshot)
        m["request"]["predicate"] = {
            "type":"equals", "key":"DATASET_KEY",
            "value":"3cba69c8-e24e-4229-8727-cfba163336fb",
        }
        with self.assertRaisesRegex(ValueError,"AND_PREDICATE"):
            validate_download_metadata(m, self.snapshot, DOI)

    def test_wrong_checklist_key_rejected(self):
        for location in ("top", "child"):
            m = good_metadata(self.snapshot)
            if location == "top":
                m["request"]["checklistKey"] = "7ddf754f-d193-4cc9-b351-99906754a03b"
            else:
                next(x for x in m["request"]["predicate"]["predicates"] if x["key"]=="TAXON_KEY")["checklistKey"]="wrong"
            with self.subTest(location=location), self.assertRaisesRegex(ValueError,"CHECKLIST"):
                validate_download_metadata(m, self.snapshot, DOI)

    def test_duplicate_status_and_licence_rejected(self):
        for field,value in [
            ("status","RUNNING"), ("license","CC_BY_4_0"),
            ("doi","10.15468/dl.other"), ("downloadLink","https://evil.invalid/a.zip"),
            ("size",0), ("totalRecords",0),
        ]:
            m=good_metadata(self.snapshot)
            m[field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_download_metadata(m,self.snapshot,DOI)

    def test_case_sensitive_predicate_rejected(self):
        m=good_metadata(self.snapshot)
        m["request"]["predicate"]["predicates"][0]["matchCase"]=True
        with self.assertRaisesRegex(ValueError,"MATCH_CASE"):
            validate_download_metadata(m,self.snapshot,DOI)

    def test_snapshot_source_change_rejected(self):
        m=good_metadata(self.snapshot)
        s=copy.deepcopy(self.snapshot)
        s["original_api_query"]=s["original_api_query"].replace("year=2024","year=2023")
        with self.assertRaises(ValueError):
            validate_download_metadata(m,s,DOI)


if __name__ == "__main__":
    unittest.main()
