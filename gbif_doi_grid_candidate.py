"""Audit a previously downloaded GBIF DwC-A for a future full-query lesson.

Only source-verified grid aggregates leave this function. This module neither
creates a GBIF download nor writes or redistributes occurrence-level records.
The returned object is an author-review candidate, not a publication release.
"""
import argparse
from collections import Counter
import csv
from hashlib import sha256
import io
import json
from math import isfinite
from pathlib import Path
from zipfile import ZipFile

from gbif_download_request import read_snapshot
from occurrence_grid import aggregate, screen
from verify_download_doi import fetch_metadata, validate_download_metadata

REQUIRED = frozenset({
    "gbifID", "countryCode", "basisOfRecord", "year", "license",
    "occurrenceStatus", "decimalLatitude", "decimalLongitude",
    "coordinateUncertaintyInMeters", "datasetKey", "hasCoordinate",
    "hasGeospatialIssues",
})
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024


def _sha256_file(path):
    hash_ = sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hash_.update(block)
    return hash_.hexdigest()


def audit_download_to_candidate(archive_path, metadata, snapshot, doi,
                                expected_zip_sha256, projector):
    """Check exact DOI/ZIP and return aggregate-only data for author review."""
    check = validate_download_metadata(metadata, snapshot, doi)
    if not isinstance(expected_zip_sha256, str) or len(expected_zip_sha256) != 64:
        raise ValueError("ARCHIVE_SHA256_REQUIRED")
    if any(c not in "0123456789abcdef" for c in expected_zip_sha256):
        raise ValueError("ARCHIVE_SHA256_MALFORMED")
    path = Path(archive_path)
    if path.stat().st_size != metadata["size"]:
        raise ValueError("ARCHIVE_SIZE_DIFFERS_FROM_VERIFIED_DOWNLOAD")
    if _sha256_file(path) != expected_zip_sha256:
        raise ValueError("ARCHIVE_SHA256_MISMATCH")
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("CORRUPT_ARCHIVE_MEMBER")
        names = archive.namelist()
        if (len(names) != len(set(names)) or
            not {"occurrence.txt", "rights.txt", "citations.txt"}.issubset(names)):
            raise ValueError("ARCHIVE_REQUIRED_MEMBERS_MISSING_OR_DUPLICATE")
        if sum(item.file_size for item in archive.infolist()) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("ARCHIVE_TOO_LARGE_FOR_REVIEW")
        rights = archive.read("rights.txt").decode("utf-8-sig")
        citations = archive.read("citations.txt").decode("utf-8-sig")
        if ("creativecommons.org/publicdomain/zero/1.0" not in rights
            or "10.15468/" not in citations):
            raise ValueError("ARCHIVE_RIGHTS_OR_CITATIONS_NOT_VERIFIED")
        with archive.open("occurrence.txt") as source:
            rows = csv.DictReader(io.TextIOWrapper(
                source, encoding="utf-8-sig", newline=""), delimiter="\t")
            if not REQUIRED.issubset(rows.fieldnames or []):
                raise ValueError("ARCHIVE_REQUIRED_OCCURRENCE_FIELDS_MISSING")
            accepted, rejected, ids = [], Counter(), set()
            all_rows = 0
            source_counts = Counter()
            qualified_counts = Counter()
            for row in rows:
                all_rows += 1
                if (row["countryCode"] != "KR" or
                    row["basisOfRecord"] != "HUMAN_OBSERVATION" or
                    row["year"] != "2024" or
                    row["license"] != "CC0_1_0" or
                    row["hasCoordinate"].lower() != "true" or
                    row["hasGeospatialIssues"].lower() != "false"):
                    raise ValueError("ARCHIVE_ROW_OUTSIDE_VERIFIED_DOWNLOAD_SELECTION")
                # Class fields are additional source guards when supplied.
                if row.get("classKey") not in (None, "", "212"):
                    raise ValueError("ARCHIVE_NON_AVES_CLASS_KEY")
                if row.get("class") not in (None, "", "Aves"):
                    raise ValueError("ARCHIVE_NON_AVES_CLASS_NAME")
                dataset = row["datasetKey"].strip()
                if not dataset:
                    raise ValueError("ARCHIVE_MISSING_DATASET_ID")
                source_counts[dataset] += 1
                record_id = row["gbifID"].strip()
                if not record_id or record_id in ids:
                    rejected["missing_or_duplicate_id"] += 1
                    continue
                ids.add(record_id)
                # Reuse the notebook's trusted licence, status, uncertainty
                # and coordinate checks, without exposing accepted records.
                # GBIF DwC-A encodes the verified CC0 licence as CC0_1_0.
                # The existing live-query screen expects its canonical URL.
                safe_row = dict(row)
                safe_row["license"] = "http://creativecommons.org/publicdomain/zero/1.0/legalcode"
                if not safe_row["coordinateUncertaintyInMeters"].strip():
                    safe_row["coordinateUncertaintyInMeters"] = None
                a, excluded = screen([safe_row], threshold=1000)
                rejected.update(excluded)
                if not a:
                    continue
                r = a[0]
                x, y = projector(r["lon"], r["lat"])
                if not isfinite(x) or not isfinite(y):
                    raise ValueError("ARCHIVE_INVALID_PROJECTED_COORDINATE")
                accepted.append((x, y))
                qualified_counts[dataset] += 1
            if all_rows != metadata["totalRecords"]:
                raise ValueError("ARCHIVE_ROW_COUNT_MISMATCH")
    if not accepted:
        raise ValueError("ARCHIVE_NO_QUALIFIED_RECORDS_UNDER_1000M_SCREEN")
    if len(accepted) + sum(rejected.values()) != all_rows:
        raise ValueError("ARCHIVE_SCREENING_COUNT_MISMATCH")
    fine = aggregate(accepted, 10000)
    coarse = aggregate(accepted, 50000)
    if sum(fine.values()) != len(accepted) or sum(coarse.values()) != len(accepted):
        raise ValueError("ARCHIVE_GRID_COUNT_MISMATCH")
    return {
        "schema": "EDS_BOOK_GBIF_FULL_DOWNLOAD_AGGREGATE_CANDIDATE_V1",
        "status": "PRIVATE_AUTHOR_REVIEW_ONLY",
        "download_doi": check["doi"],
        "download_key": check["download_key"],
        "archive_sha256": expected_zip_sha256,
        "source_records": all_rows,
        "accepted_count": len(accepted),
        "excluded": dict(sorted(rejected.items())),
        "source_dataset_counts": dict(sorted(source_counts.items())),
        "accepted_dataset_counts": dict(sorted(qualified_counts.items())),
        "illustrative_coordinate_uncertainty_threshold_m": 1000,
        "projected_crs": "EPSG:32652",
        "grid_10km": [[x, y, n] for (x, y), n in sorted(fine.items())],
        "grid_50km": [[x, y, n] for (x, y), n in sorted(coarse.items())],
        "individual_records_redistributed": False,
        "provider_license_metadata_inspected": True,
        "publisher_by_publisher_rights_review_complete": False,
        "editorial_and_binder_review_complete": False,
    }


def main():
    p = argparse.ArgumentParser(description="Offline verified GBIF grid candidate")
    p.add_argument("--doi", required=True)
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--sha256", required=True)
    p.add_argument("--snapshot", default="data/first-page-grids-20261026.json")
    p.add_argument("--metadata", type=Path, help="Locally archived metadata; otherwise read-only GBIF GET")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    metadata = (json.loads(args.metadata.read_text(encoding="utf8"))
                if args.metadata else fetch_metadata(args.doi))
    from pyproj import Transformer
    proj = Transformer.from_crs("EPSG:4326", "EPSG:32652", always_xy=True).transform
    result = audit_download_to_candidate(
        args.archive, metadata, read_snapshot(args.snapshot), args.doi,
        args.sha256, proj)
    if args.output.exists():
        p.error("OUTPUT_ALREADY_EXISTS_NO_OVERWRITE")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf8")
    print("AUTHOR_REVIEW_AGGREGATE_ONLY " + str(args.output))


if __name__ == "__main__":
    main()
