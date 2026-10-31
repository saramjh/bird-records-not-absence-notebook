"""Prepare (but NEVER submit) an authenticated GBIF occurrence-download request.

This offline manifest describes a *new full-result* download. It cannot
retroactively version the historical nonrandom first-100-record snapshot.

Submission requires the researcher's own authenticated GBIF account and a
separate, explicitly authorized action. No credential/network code here.
References: https://techdocs.gbif.org/en/data-use/api-downloads
"""
import argparse
import copy
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

BACKBONE = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"
SCHEMA = "EDS_BOOK_GBIF_DERIVED_GRID_SNAPSHOT_V1"
EXPECTED_SEARCH = {
    "country": ["KR"],
    "taxonKey": ["212"],
    "basisOfRecord": ["HUMAN_OBSERVATION"],
    "year": ["2024"],
    "license": ["CC0_1_0"],
    "hasCoordinate": ["true"],
    "hasGeospatialIssue": ["false"],
    "limit": ["100"],
    "offset": ["0"],
}


def read_snapshot(path):
    """Read snapshot *metadata*, not occurrence-level private coordinates."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def expected_predicate():
    """Taxon 212 belongs to the explicitly pinned historical GBIF Backbone."""
    items = [
        ("COUNTRY", "KR"),
        ("TAXON_KEY", "212"),
        ("BASIS_OF_RECORD", "HUMAN_OBSERVATION"),
        ("YEAR", "2024"),
        ("LICENSE", "CC0_1_0"),
        ("HAS_COORDINATE", "true"),
        ("HAS_GEOSPATIAL_ISSUE", "false"),
    ]
    predicates = []
    for key, value in items:
        item = {"type": "equals", "key": key, "value": value}
        if key == "TAXON_KEY":
            item["checklistKey"] = BACKBONE
        predicates.append(item)
    return {"type": "and", "predicates": predicates}


def build_request(snapshot, email):
    """Fail closed on provenance/source drift; return a no-send GBIF JSON body."""
    if not isinstance(snapshot, dict):
        raise ValueError("SNAPSHOT_NOT_OBJECT")
    if snapshot.get("schema") != SCHEMA:
        raise ValueError("SNAPSHOT_SCHEMA_CHANGED")
    if snapshot.get("GBIF_occurrence_download_doi") is not None:
        raise ValueError("SNAPSHOT_ALREADY_HAS_A_DOWNLOAD_DOI")
    if snapshot.get("query_country") != "KR" or snapshot.get("query_year") != 2024:
        raise ValueError("SNAPSHOT_QUERY_METADATA_CHANGED")
    if snapshot.get("first_page_limit") != 100 or snapshot.get("rows_in_page") != 100:
        raise ValueError("SNAPSHOT_SAMPLE_SIZE_CHANGED")
    source = urlsplit(snapshot.get("original_api_query", ""))
    if (
        source.scheme != "https"
        or source.netloc != "api.gbif.org"
        or source.path != "/v1/occurrence/search"
        or source.query == ""
        or source.fragment
        or parse_qs(source.query, keep_blank_values=True) != EXPECTED_SEARCH
    ):
        raise ValueError("SNAPSHOT_API_SOURCE_FILTERS_CHANGED")
    if not isinstance(email, str) or not re.fullmatch(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,63}", email
    ):
        raise ValueError("INVALID_GBIF_NOTIFICATION_EMAIL")
    return {
        "notificationAddresses": [email],
        "sendNotification": True,
        "format": "DWCA",
        "checklistKey": BACKBONE,
        "predicate": copy.deepcopy(expected_predicate()),
    }


def main():
    p = argparse.ArgumentParser(description="Build an offline GBIF download request WITHOUT sending")
    p.add_argument("--email", required=True, help="Owner's GBIF account notification email; no passwords")
    p.add_argument("--snapshot", default="data/first-page-grids-20261026.json")
    p.add_argument("--output", help="Optional local JSON file, never sent")
    args = p.parse_args()
    try:
        result = build_request(read_snapshot(args.snapshot), args.email)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        p.error(str(error))
    formatted = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(formatted, encoding="utf-8")
        print("OFFLINE_REQUEST_ONLY_NOT_SUBMITTED")
    else:
        print(formatted, end="")


if __name__ == "__main__":
    main()
