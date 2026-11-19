"""Read-only check that a GBIF occurrence-download DOI freezes the intended query.

This is a metadata preflight for a FUTURE full-result DOI, not an attempt to
recreate the historical first-100 search sample. It never submits a download,
reads GBIF credentials, or fetches occurrence-level rows.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

from gbif_download_request import BACKBONE, build_request, read_snapshot

DOI_PATTERN = re.compile(r"10\.15468/dl\.[a-z0-9]+", re.ASCII)
API_BASE = "https://api.gbif.org/v1/occurrence/download/"


def _equals_fields(node):
    if not isinstance(node, dict) or str(node.get("type", "")).lower() != "equals":
        raise ValueError("DOWNLOAD_PREDICATE_NOT_EXACT_EQUALS")
    if node.get("matchCase", False) is not False:
        raise ValueError("DOWNLOAD_PREDICATE_MATCH_CASE_CHANGED")
    key, value = node.get("key"), node.get("value")
    if not isinstance(key, str) or not isinstance(value, (str, int, bool)):
        raise ValueError("DOWNLOAD_PREDICATE_INVALID_VALUE")
    if key not in {
        "COUNTRY", "TAXON_KEY", "BASIS_OF_RECORD", "YEAR", "LICENSE",
        "HAS_COORDINATE", "HAS_GEOSPATIAL_ISSUE",
    }:
        raise ValueError("DOWNLOAD_PREDICATE_UNEXPECTED_FILTER")
    if key == "TAXON_KEY" and node.get("checklistKey", BACKBONE) != BACKBONE:
        raise ValueError("DOWNLOAD_TAXON_CHECKLIST_DRIFT")
    if key != "TAXON_KEY" and "checklistKey" in node:
        raise ValueError("DOWNLOAD_UNEXPECTED_CHECKLIST")
    return key, str(value).lower() if key.startswith("HAS_") else str(value)


def validate_download_metadata(metadata, snapshot, doi):
    """Reject any source-predicate drift before considering a DOI citable."""
    if not isinstance(doi, str) or DOI_PATTERN.fullmatch(doi) is None:
        raise ValueError("INVALID_DOWNLOAD_DOI")
    if not isinstance(metadata, dict):
        raise ValueError("DOWNLOAD_METADATA_NOT_OBJECT")
    if metadata.get("doi") != doi:
        raise ValueError("DOWNLOAD_DOI_DOES_NOT_MATCH_METADATA")
    if metadata.get("status") != "SUCCEEDED":
        raise ValueError("DOWNLOAD_NOT_SUCCEEDED")
    key = metadata.get("key")
    if not isinstance(key, str) or re.fullmatch(r"\d{7}-\d{15}", key) is None:
        raise ValueError("DOWNLOAD_KEY_INVALID")
    link = metadata.get("downloadLink")
    if link != API_BASE + "request/" + key + ".zip":
        raise ValueError("DOWNLOAD_LINK_NOT_EXPECTED_GBIF_ARCHIVE")
    if not isinstance(metadata.get("totalRecords"), int) or metadata["totalRecords"] < 1:
        raise ValueError("DOWNLOAD_EMPTY_OR_INVALID_RECORD_COUNT")
    if not isinstance(metadata.get("size"), int) or metadata["size"] < 1:
        raise ValueError("DOWNLOAD_INVALID_SIZE")
    if metadata.get("license") not in {
        "CC0_1_0",
        "http://creativecommons.org/publicdomain/zero/1.0/legalcode",
        "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
    }:
        raise ValueError("DOWNLOAD_NOT_CC0")
    request = metadata.get("request")
    if not isinstance(request, dict) or request.get("format") != "DWCA":
        raise ValueError("DOWNLOAD_NOT_DWCA")
    if request.get("checklistKey") != BACKBONE:
        raise ValueError("DOWNLOAD_REQUEST_CHECKLIST_DRIFT")
    predicate = request.get("predicate")
    if not isinstance(predicate, dict) or str(predicate.get("type", "")).lower() != "and":
        raise ValueError("DOWNLOAD_NOT_AND_PREDICATE")
    children = predicate.get("predicates")
    if not isinstance(children, list) or len(children) != 7:
        raise ValueError("DOWNLOAD_PREDICATE_COUNT_CHANGED")

    observed = dict(_equals_fields(x) for x in children)
    if len(observed) != len(children):
        raise ValueError("DOWNLOAD_DUPLICATE_PREDICATE")
    expected_request = build_request(snapshot, "source-review@example.org")
    expected = dict(_equals_fields(x) for x in expected_request["predicate"]["predicates"])
    if observed != expected:
        raise ValueError("DOWNLOAD_SOURCE_FILTERS_DIFFER_FROM_SNAPSHOT")
    normalized = json.dumps(observed, sort_keys=True, separators=(",", ":"))
    return {
        "schema": "EDS_BOOK_GBIF_DOWNLOAD_METADATA_PREFLIGHT_V1",
        "doi": doi,
        "download_key": key,
        "source_records": metadata["totalRecords"],
        "archive_size_bytes": metadata["size"],
        "requested_selection_sha256": sha256(normalized.encode("utf-8")).hexdigest(),
        "exact_full_query_metadata_match": True,
        "archive_sha256_verified": False,
        "archive_contents_audited": False,
        "not_the_historical_first_100_sample": True,
        "no_download_or_provider_write": True,
    }


def fetch_metadata(doi):
    if DOI_PATTERN.fullmatch(doi) is None:
        raise ValueError("INVALID_DOWNLOAD_DOI")
    req = Request(API_BASE + doi, headers={
        "User-Agent": "KoreAves-EDSBook-DOI-metadata-preflight/1.0",
        "Accept": "application/json",
    })
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description="Read-only GBIF DOI metadata preflight")
    parser.add_argument("--doi", required=True)
    parser.add_argument("--snapshot", default="data/first-page-grids-20261026.json")
    parser.add_argument("--metadata-json", help="Use local synthetic metadata instead of a GET")
    args = parser.parse_args()
    metadata = json.loads(Path(args.metadata_json).read_text(encoding="utf-8")) if args.metadata_json else fetch_metadata(args.doi)
    result = validate_download_metadata(metadata, read_snapshot(args.snapshot), args.doi)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
