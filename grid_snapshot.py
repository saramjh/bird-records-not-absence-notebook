"""Validate a safe, derived, nonrandom GBIF grid demonstration snapshot.

Only aggregate 10-km cell counts, not original individual coordinates or IDs,
are shipped in the repository. A dataset DOI is NOT an occurrence-download DOI.
"""
import json
from collections import Counter
from pathlib import Path

SCHEMA = "EDS_BOOK_GBIF_DERIVED_GRID_SNAPSHOT_V1"

def load_snapshot(path):
    """Load only an internally consistent published teaching aggregate."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unrecognized snapshot schema")
    if data.get("GBIF_occurrence_download_doi") is not None:
        raise ValueError("unverified occurrence-download DOI must not be asserted")
    if data.get("projected_crs") != "EPSG:32652" or data.get("grid_m") != 10000:
        raise ValueError("unsupported projected aggregation")
    if data.get("first_page_limit") != 100 or data.get("query_country") != "KR":
        raise ValueError("changed scientific source selection")
    if not isinstance(data.get("accepted_count"), int) or data["accepted_count"] <= 0:
        raise ValueError("invalid screened record count")
    rejected = data.get("excluded")
    if not isinstance(rejected, dict) or any(not isinstance(v,int) or v<0 for v in rejected.values()):
        raise ValueError("invalid exclusion counts")
    if data.get("rows_in_page") != data["accepted_count"] + sum(rejected.values()):
        raise ValueError("screening audit mismatch")
    first_counts = data.get("first_page_dataset_counts")
    accepted_counts = data.get("accepted_dataset_counts")
    dois = data.get("dataset_dois")
    if not all(isinstance(x,dict) for x in (first_counts,accepted_counts,dois)):
        raise ValueError("missing provenance")
    if sum(first_counts.values()) != data["rows_in_page"] or sum(accepted_counts.values()) != data["accepted_count"]:
        raise ValueError("publisher count mismatch")
    if set(first_counts) != set(dois) or not set(accepted_counts).issubset(set(first_counts)):
        raise ValueError("missing publisher citation")
    fine, coarse = derive_grids(data.get("cells_10km"))
    if sum(fine.values()) != data["accepted_count"] or sum(coarse.values()) != data["accepted_count"]:
        raise ValueError("published grid does not conserve records")
    if len(fine) != data.get("occupied_cells_10km") or len(coarse) != data.get("occupied_cells_50km"):
        raise ValueError("published occupied-cell counts differ")
    if data.get("reported_uncertainty_max_m") != 1000:
        raise ValueError("screening threshold mismatch")
    return data

def derive_grids(cells):
    """A 10-km projected cell fits exactly inside one origin-aligned 50-km cell."""
    if not isinstance(cells,list) or not cells:
        raise ValueError("no grid cells")
    fine = {}
    coarse = Counter()
    for row in cells:
        if (not isinstance(row,list) or len(row)!=3 or
                any(type(v) is not int for v in row)):
            raise ValueError("malformed cell/count entry")
        gx,gy,n = row
        if n <= 0 or (gx,gy) in fine:
            raise ValueError("duplicate or empty cell")
        fine[(gx,gy)] = n
        coarse[(gx//5,gy//5)] += n
    return fine,dict(coarse)
