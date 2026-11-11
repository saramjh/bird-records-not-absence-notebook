"""Offline synthetic page tests. No network or real bird records."""

import json
import unittest

from audit_live_gbif_search import QUERY, audit_full_search


def sample(record_id, uncertainty, dataset="synthetic-dataset"):
    return {
        "gbifID": record_id, "datasetKey": dataset,
        "license": "http://creativecommons.org/publicdomain/zero/1.0/legalcode",
        "countryCode": "KR", "basisOfRecord": "HUMAN_OBSERVATION",
        "year": 2024, "decimalLatitude": 36.5, "decimalLongitude": 127.4,
        "coordinateUncertaintyInMeters": uncertainty,
        "recordedBy": "Synthetic Tester",
    }


def mock_pages(*pages, totals=None):
    totals = totals or [sum(map(len, pages))] * len(pages)
    def get(parameters):
        offset = int(parameters["offset"])
        length = int(parameters["limit"])
        page = offset // length
        return {"count": totals[page], "results": pages[page]}
    return get


class LiveQueryAuditTests(unittest.TestCase):
    def test_full_query_and_screening_conserve_and_use_all_pages(self):
        rows1 = [sample("one", 500), sample("two", None)]
        rows2 = [sample("three", 1001), sample("four", 1000, "other-dataset")]
        report = audit_full_search(mock_pages(rows1, rows2), page_size=2)
        self.assertEqual(report["source_records"], 4)
        self.assertEqual(report["pages"], 2)
        self.assertEqual(report["accepted_after_illustrative_1000m_screen"], 2)
        self.assertEqual(report["excluded"], {
            "above_illustrative_threshold": 1, "uncertainty_missing": 1,
        })
        self.assertEqual(report["accepted_by_dataset_key"], {
            "other-dataset": 1, "synthetic-dataset": 1,
        })
        self.assertIsNone(report["versioned_occurrence_download_doi"])

    def test_no_observation_level_data_in_report(self):
        report = audit_full_search(mock_pages([sample("synthetic-private-id", 100)]))
        serial = json.dumps(report)
        for secret in ("gbifID", "decimalLatitude", "decimalLongitude",
                       "recordedBy", "Synthetic Tester", "synthetic-private-id"):
            self.assertNotIn(secret, serial)
        self.assertFalse(report["raw_occurrences_exported"])

    def test_api_total_changes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "count drift"):
            audit_full_search(mock_pages([sample("a", 1)], [sample("b", 1)],
                                         totals=[2, 3]), page_size=1)

    def test_missing_api_page_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "sized API page"):
            audit_full_search(mock_pages([sample("a", 1)], [], totals=[2, 2]), page_size=1)

    def test_duplicate_across_pages_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate occurrence"):
            audit_full_search(mock_pages([sample("a", 1)], [sample("a", 1)]),
                              page_size=1)

    def test_reject_bad_page_size(self):
        for size in (0, 301, -1):
            with self.assertRaisesRegex(ValueError, "invalid page size"):
                audit_full_search(mock_pages([sample("a", 1)]), page_size=size)

    def test_query_is_original_not_download_mutation(self):
        self.assertEqual(QUERY["country"], "KR")
        self.assertEqual(QUERY["year"], "2024")
        self.assertEqual(QUERY["taxonKey"], "212")
        self.assertEqual(QUERY["license"], "CC0_1_0")
        self.assertEqual(QUERY["hasGeospatialIssue"], "false")


if __name__ == "__main__":
    unittest.main()
