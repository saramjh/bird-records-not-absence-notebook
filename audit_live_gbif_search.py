"""Audit the complete current GBIF search without publishing occurrence rows.

An opt-in, read-only API probe, not a frozen occurrence download.
No raw records, coordinates, observer information or GBIF IDs are written.
"""

from collections import Counter
from datetime import datetime, timezone
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from occurrence_grid import screen


API_URL = "https://api.gbif.org/v1/occurrence/search"
QUERY = {
    "country": "KR",
    "taxonKey": "212",
    "basisOfRecord": "HUMAN_OBSERVATION",
    "year": "2024",
    "license": "CC0_1_0",
    "hasCoordinate": "true",
    "hasGeospatialIssue": "false",
}
PAGE_SIZE = 300
MAX_ROWS = 10000  # Fail closed rather than silently truncate a growing search.


def fetch_page(parameters):
    """Unauthenticated GET. No GBIF download or export request is created."""
    url = API_URL + "?" + urlencode(parameters)
    request = Request(url, headers={
        "User-Agent": "KoreAves-EDSBook-source-qualification/1.0",
    })
    with urlopen(request, timeout=45) as response:
        return json.load(response)


def audit_full_search(fetcher=fetch_page, *, page_size=PAGE_SIZE, observed_at=None):
    if not isinstance(page_size, int) or not 1 <= page_size <= PAGE_SIZE:
        raise ValueError("invalid page size")
    rows = []
    seen_ids = set()
    expected_total = None
    pages = 0
    while expected_total is None or len(rows) < expected_total:
        if len(rows) >= MAX_ROWS:
            raise ValueError("search exceeds audited maximum rows")
        parameters = {**QUERY, "limit": str(page_size), "offset": str(len(rows))}
        result = fetcher(parameters)
        total = result.get("count")
        chunk = result.get("results")
        if not isinstance(total, int) or total <= 0 or total > MAX_ROWS:
            raise ValueError("unbounded or invalid result count")
        if expected_total is None:
            expected_total = total
        if total != expected_total:
            raise ValueError("API count drift between pages")
        if not isinstance(chunk, list) or len(chunk) != min(page_size, total - len(rows)):
            raise ValueError("missing or unexpectedly sized API page")
        for record in chunk:
            if not isinstance(record, dict):
                raise ValueError("malformed occurrence")
            record_id = str(record.get("gbifID") or "")
            if record_id and record_id in seen_ids:
                raise ValueError("duplicate occurrence across pages; review before retry")
            if record_id:
                seen_ids.add(record_id)
        rows.extend(chunk)
        pages += 1

    accepted, excluded = screen(rows, threshold=1000)
    if len(accepted) + sum(excluded.values()) != len(rows):
        raise ValueError("screening does not conserve source records")
    all_sources = dict(sorted(Counter(str(r.get("datasetKey") or "") for r in rows).items()))
    accepted_sources = dict(sorted(Counter(r["datasetKey"] for r in accepted).items()))
    return {
        "schema": "EDS_BOOK_LIVE_GBIF_FULL_QUERY_AGGREGATE_V1",
        "observed_at_utc": (observed_at or datetime.now(timezone.utc)).isoformat(),
        "api": API_URL,
        "query": dict(QUERY),
        "source_records": len(rows),
        "source_datasets_by_key": all_sources,
        "pages": pages,
        "page_size": page_size,
        "accepted_after_illustrative_1000m_screen": len(accepted),
        "accepted_by_dataset_key": accepted_sources,
        "excluded": dict(sorted(excluded.items())),
        "versioned_occurrence_download_doi": None,
        "single_frozen_snapshot_guaranteed": False,
        "raw_occurrences_exported": False,
        "raw_coordinates_exported": False,
        "observer_details_exported": False,
    }


def main():
    print(json.dumps(audit_full_search(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
