"""Read-only audit of an existing published GBIF occurrence download.

This fixed, single-source archive cannot replace the notebook's original
nonrandom API first-page selection under its current uncertainty threshold.
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

DOWNLOAD_DOI = "10.15468/dl.u7tcq5"
DATASET_DOI = "10.15468/ya2fjz"
DATASET_KEY = "3cba69c8-e24e-4229-8727-cfba163336fb"
ZIP_SHA256 = "9ed28c2cfb96d83a0f0bdcba90598474efc1f34f675619c049da308ffce8c098"
REQUIRED_FIELDS = {
    "year", "datasetKey", "license", "basisOfRecord", "countryCode",
    "hasCoordinate", "hasGeospatialIssues", "occurrenceStatus", "decimalLatitude",
    "decimalLongitude", "coordinateUncertaintyInMeters", "gbifID",
}


def audit_archive(path, *, expected_sha256=ZIP_SHA256, exact_cohort=True):
    """Return aggregate source checks. Never return IDs or coordinates."""
    source = Path(path)
    observed_hash = sha256(source.read_bytes()).hexdigest()
    if expected_sha256 and observed_hash != expected_sha256:
        raise ValueError("archived GBIF download checksum mismatch")
    totals = Counter()
    years = Counter()
    seen_ids = set()
    with ZipFile(source) as archive:
        if archive.testzip() is not None:
            raise ValueError("bad GBIF archive member")
        if not {"occurrence.txt", "rights.txt", "citations.txt"}.issubset(archive.namelist()):
            raise ValueError("missing required GBIF archive entry")
        rights = archive.read("rights.txt").decode("utf-8-sig")
        citations = archive.read("citations.txt").decode("utf-8-sig")
        if "creativecommons.org/publicdomain/zero/1.0" not in rights:
            raise ValueError("dataset archive rights are not CC0")
        if DATASET_DOI not in citations:
            raise ValueError("source dataset citation missing")
        with archive.open("occurrence.txt") as stream:
            reader = csv.DictReader(
                io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""),
                delimiter="\t",
            )
            if not REQUIRED_FIELDS.issubset(reader.fieldnames or ()):
                raise ValueError("required DwC fields missing")
            for row in reader:
                totals["all_records"] += 1
                years[row["year"]] += 1
                if (row["datasetKey"] != DATASET_KEY
                    or row["license"] != "CC0_1_0"
                    or row["basisOfRecord"] != "HUMAN_OBSERVATION"
                    or row["countryCode"] != "KR"):
                    raise ValueError("record source, country, basis or licence drift")
                if row["year"] != "2024":
                    continue
                totals["year_2024"] += 1
                if row["occurrenceStatus"].strip().upper() not in ("DETECTED", "PRESENT"):
                    totals["excluded_non_detection_or_unknown_status"] += 1
                    continue
                if (row["hasCoordinate"] == "true"
                    and row["decimalLatitude"].strip()
                    and row["decimalLongitude"].strip()):
                    totals["with_coordinate_field"] += 1
                if row["hasGeospatialIssues"] == "false":
                    totals["without_reported_geospatial_issue"] += 1
                record_id = row["gbifID"].strip()
                unique_id = bool(record_id) and record_id not in seen_ids
                if record_id:
                    seen_ids.add(record_id)
                reported = row["coordinateUncertaintyInMeters"].strip()
                if reported:
                    totals["with_reported_coordinate_uncertainty"] += 1
                else:
                    totals["missing_reported_coordinate_uncertainty"] += 1
                    continue
                # Match the existing notebook's <=1,000 m uncertainty screen.
                # Having a nonempty uncertainty field alone is insufficient.
                try:
                    uncertainty = float(reported)
                    latitude = float(row["decimalLatitude"])
                    longitude = float(row["decimalLongitude"])
                except (ValueError, TypeError):
                    continue
                if (not unique_id
                    or not all(isfinite(v) for v in (uncertainty, latitude, longitude))
                    or not 0 <= uncertainty <= 1000
                    or not -90 <= latitude <= 90
                    or not -180 <= longitude <= 180
                    or row["hasCoordinate"] != "true"
                    or row["hasGeospatialIssues"] != "false"):
                    continue
                totals["strict_uncertainty_threshold_usable_records"] += 1
    if exact_cohort and (
        totals["all_records"] != 3359
        or totals["year_2024"] != 3207
        or totals["with_coordinate_field"] != 3207
        or totals["missing_reported_coordinate_uncertainty"] != 3207
    ):
        raise ValueError("download cohort count drift")
    return {
        "download_doi": DOWNLOAD_DOI,
        "dataset_doi": DATASET_DOI,
        "download_sha256": observed_hash,
        "source_record_count": totals["all_records"],
        "year_counts": dict(sorted(years.items())),
        "year_2024_records": totals["year_2024"],
        "year_2024_excluded_non_detection_or_unknown_status":
            totals["excluded_non_detection_or_unknown_status"],
        "year_2024_with_coordinate_field": totals["with_coordinate_field"],
        "year_2024_without_reported_geospatial_issue":
            totals["without_reported_geospatial_issue"],
        "year_2024_with_reported_coordinate_uncertainty":
            totals["with_reported_coordinate_uncertainty"],
        "year_2024_missing_reported_coordinate_uncertainty":
            totals["missing_reported_coordinate_uncertainty"],
        "existing_notebook_first_page_selection_replaced": False,
        "strict_uncertainty_threshold_usable_records":
            totals["strict_uncertainty_threshold_usable_records"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Previously obtained GBIF DwC-A zip; no network")
    args = parser.parse_args()
    print(json.dumps(audit_archive(args.archive), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
