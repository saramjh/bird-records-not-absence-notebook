"""Reproduce a separate, provisional teaching grid from an existing GBIF DOI.

This is an explicitly *unknown-coordinate-precision* illustration, NOT a
replacement for the notebook's strict <=1,000 m input. It never distributes
original occurrence rows, observer identifiers or raw coordinates.

The already-published download is 10.15468/dl.u7tcq5 (NSMK, CC0), whose
2024 records all lack reported coordinate uncertainty. A grid bin does not
establish that those recorded positions are accurate at that resolution.
"""
import argparse
import csv
from hashlib import sha256
import io
import json
from math import isfinite
from pathlib import Path
from zipfile import ZipFile

from audit_existing_gbif_doi import (
    audit_archive, DATASET_DOI, DATASET_KEY, DOWNLOAD_DOI, ZIP_SHA256,
)
from occurrence_grid import aggregate


DOWNLOAD_KEY = "0015299-260903145123482"
DOWNLOAD_LINK = (
    "https://api.gbif.org/v1/occurrence/download/request/"
    "0015299-260903145123482.zip"
)
RIGHTS = "http://creativecommons.org/publicdomain/zero/1.0/legalcode"


def _validate_download_metadata(metadata, archive, *, exact_cohort):
    if not isinstance(metadata, dict):
        raise ValueError("DOWNLOAD_METADATA_REQUIRED")
    expected = {
        "doi": DOWNLOAD_DOI,
        "key": DOWNLOAD_KEY,
        "status": "SUCCEEDED",
        "license": RIGHTS,
        "downloadLink": DOWNLOAD_LINK,
    }
    # For synthetic offline unit tests the download URL may be omitted, but
    # publication-grade source checking must include it.
    for key, required in expected.items():
        if (exact_cohort or key != "downloadLink" or key in metadata):
            if metadata.get(key) != required:
                raise ValueError("DOWNLOAD_METADATA_" + key.upper() + "_MISMATCH")
    req = metadata.get("request")
    if (not isinstance(req, dict)
        or req.get("type") != "OCCURRENCE"
        or req.get("format") != "DWCA"
        or req.get("predicate", {}).get("type") != "equals"
        or req["predicate"].get("key") != "DATASET_KEY"
        or req["predicate"].get("value") != DATASET_KEY):
        raise ValueError("DOWNLOAD_SELECTION_NOT_NSMK_DATASET")
    if not isinstance(metadata.get("size"), int) or metadata["size"] != archive.stat().st_size:
        raise ValueError("DOWNLOAD_METADATA_SIZE_MISMATCH")
    if not isinstance(metadata.get("totalRecords"), int) or metadata["totalRecords"] < 1:
        raise ValueError("DOWNLOAD_METADATA_COUNT_INVALID")
    if exact_cohort and metadata["totalRecords"] != 3359:
        raise ValueError("DOWNLOAD_METADATA_COHORT_COUNT_MISMATCH")


def build_unknown_precision_candidate(archive_path, metadata, projector, *,
                                      expected_sha256=ZIP_SHA256, exact_cohort=True):
    """Return aggregate-only private research artifact after strict source checks.

    'Unknown precision' is a distinct teaching experiment: it must not be
    merged with the strict original 1,000m screen or described as ground truth.
    A caller supplies a projected-coordinate transform (EPSG:32652 in CLI).
    """
    path = Path(archive_path)
    if exact_cohort and expected_sha256 is None:
        raise ValueError("PRODUCTION_ARCHIVE_SHA_REQUIRED")
    _validate_download_metadata(metadata, path, exact_cohort=exact_cohort)
    # archive audit checks rights.txt, citations.txt, all-record publisher and
    # occurrence licences, status field, and original source cohort totals.
    audit = audit_archive(path, expected_sha256=expected_sha256,
                          exact_cohort=exact_cohort)
    if metadata["totalRecords"] != audit["source_record_count"]:
        raise ValueError("DOWNLOAD_ARCHIVE_RECORD_COUNT_MISMATCH")
    points = []
    seen = set()
    excluded_status = 0
    with ZipFile(path) as z:
        with z.open("occurrence.txt") as b:
            reader = csv.DictReader(
                io.TextIOWrapper(b, encoding="utf-8-sig", newline=""),
                delimiter="\t")
            for row in reader:
                if row["year"] != "2024":
                    continue
                status = row["occurrenceStatus"].strip().upper()
                if status not in ("PRESENT", "DETECTED"):
                    excluded_status += 1
                    continue
                if (row["hasCoordinate"].lower() != "true"
                    or row["hasGeospatialIssues"].lower() != "false"):
                    raise ValueError("SOURCE_COORDINATE_FLAG_NOT_QUALIFIED")
                rid = row["gbifID"].strip()
                if not rid or rid in seen:
                    raise ValueError("MISSING_OR_DUPLICATE_GBIF_ID")
                seen.add(rid)
                # The previously published NSMK archive supplies positions but
                # does not supply their precision. 0 or an arbitrary threshold
                # is not imputed. If source metadata changes, stop for review.
                if row["coordinateUncertaintyInMeters"].strip():
                    raise ValueError("UNREPORTED_PRECISION_EXPECTED")
                try:
                    lat = float(row["decimalLatitude"])
                    lon = float(row["decimalLongitude"])
                except (TypeError, ValueError) as error:
                    raise ValueError("SOURCE_COORDINATE_INVALID") from error
                if not (isfinite(lat) and isfinite(lon)
                        and -90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("SOURCE_COORDINATE_INVALID")
                x, y = projector(lon, lat)
                if not (isfinite(x) and isfinite(y)):
                    raise ValueError("PROJECTED_COORDINATE_INVALID")
                points.append((x, y))
    count = len(points)
    if count == 0:
        raise ValueError("NO_ELIGIBLE_2024_RECORDS")
    if count + excluded_status != audit["year_2024_records"]:
        raise ValueError("SOURCE_SCREENING_RECORDS_NOT_CONSERVED")
    if exact_cohort and (count != 3207 or excluded_status != 0):
        raise ValueError("ORIGINAL_2024_COHORT_UNEXPECTED")
    fine = aggregate(points, 10000)
    coarse = aggregate(points, 50000)
    if sum(fine.values()) != count or sum(coarse.values()) != count:
        raise ValueError("DERIVED_GRID_COUNT_NOT_CONSERVED")
    return {
        "schema": "EDS_BOOK_NSMK_DOI_UNKNOWN_COORDINATE_PRECISION_GRID_V1",
        "status": "PRIVATE_AUTHOR_REVIEW_ONLY",
        "source_download_doi": DOWNLOAD_DOI,
        "source_download_key": DOWNLOAD_KEY,
        "source_dataset_doi": DATASET_DOI,
        "source_dataset_key": DATASET_KEY,
        "source_archive_sha256": sha256(path.read_bytes()).hexdigest(),
        "source_archive_bytes": path.stat().st_size,
        "source_license": "CC0 1.0 (source occurrence records)",
        "source_total_records": audit["source_record_count"],
        "source_year_2024_records": audit["year_2024_records"],
        "accepted_count": count,
        "unreported_coordinate_uncertainty_count": count,
        "excluded_non_detection_or_unknown_status": excluded_status,
        "coordinate_uncertainty_reported_m": None,
        "coordinates_are_verified_to_grid_resolution": False,
        "original_coordinates_released": False,
        "original_observer_information_released": False,
        "original_record_ids_released": False,
        "this_is_not_the_1000m_strict_snapshot": True,
        "this_is_not_the_original_mutable_100_row_sample": True,
        "projected_crs": "EPSG:32652",
        "analyst_grid_sizes_m": [10000, 50000],
        "grid_10km": [[x, y, n] for (x, y), n in sorted(fine.items())],
        "grid_50km": [[x, y, n] for (x, y), n in sorted(coarse.items())],
        "licence_and_citation_review": "Source ZIP rights/citations checked, separate author/publisher QA outstanding",
        "binder_and_editorial_review_complete": False,
        "not_an_absence_abundance_or_sighting_prediction": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path,
                        help="Exact source GBIF DOI public JSON, previously GET-fetched")
    parser.add_argument("--output", required=True, type=Path,
                        help="Private candidate JSON. Will not overwrite.")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("OUTPUT_ALREADY_EXISTS_NO_OVERWRITE")
    meta = json.loads(args.metadata.read_text(encoding="utf-8"))
    from pyproj import Transformer
    projector = Transformer.from_crs(
        "EPSG:4326", "EPSG:32652", always_xy=True).transform
    candidate = build_unknown_precision_candidate(args.archive, meta, projector)
    args.output.write_text(
        json.dumps(candidate, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "status": candidate["status"],
        "saved": str(args.output),
        "download_doi": candidate["source_download_doi"],
        "records": candidate["accepted_count"],
        "uncertainty_reported": False,
        "occupied_10km_cells": len(candidate["grid_10km"]),
        "occupied_50km_cells": len(candidate["grid_50km"]),
        "not_published": True,
    }, ensure_ascii=True))


if __name__ == "__main__":
    main()
