# When a bird map looks empty

A preparation-stage Python notebook for Environmental Data Science Book idea [#14](https://github.com/eds-book/notebooks-ideas/issues/14), created from the [official Python template](https://github.com/eds-book/template_python).

**Author:** Jihun Oh. The question arose while developing [KoreAves](https://koreaves.com); KoreAves is a disclosed optional case study, NOT this notebook's original data provider. No EDS Book peer review, Binder validation or publication is claimed.

The notebook screens CC0-licensed records from a **bounded first page** of the live GBIF occurrence API, distinguishes missing coordinate uncertainty from zero uncertainty, compares 10 km and 50 km analyst-defined projected grids, and explains why record counts and blank cells do NOT establish bird abundance or absence.

This page of the live API is non-random, not versioned and may change. It is **not a completed data product**. Before review, replace it with a [DOI-versioned GBIF occurrence download](https://www.gbif.org/citation-guidelines), audit dataset publisher credits and licence, and test the final notebook through Binder. No third-party photos or sound recordings are distributed. Fine-scale occurrence coordinates are not stored in the repository.

## Run

Use the template's environment.yml with conda/mamba, open notebook.ipynb, and run all cells offline using the bundled derived grid snapshot (LIVE_GBIF = False). Non-network tests: python -m unittest discover -p 'test_*.py'.

Only the `preparation` branch carries this candidate notebook. The template workflow was temporarily extended for author-side offline verification on 27 October, then restored byte-for-byte to the upstream EDS Book version (commit [`0ed35d9`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/0ed35d9732fdf69ad5bdd7fe098ac4f0f97464cd)).

## Provenance, citation and execution QA (2026-10-26)

The GBIF query's first 100 individual-record CC0 occurrences contained 61 from [iNaturalist](https://doi.org/10.15468/ab3s5x) and 39 from [NSMK local biodiversity recordings](https://doi.org/10.15468/ya2fjz). The overall iNaturalist dataset licence is **CC BY-NC 4.0** while some individual records are CC0; photos and sounds must be licensed separately. These two DOIs identify the contributing **datasets**, not a stable GBIF occurrence **download** for the sampled query. No precise locations or imagery were added to this repository.

The notebook executed all four code cells on isolated Windows Python 3.13 (numpy 2.1.3, matplotlib 3.9.4, pyproj 3.7.1, nbclient 0.10.2), screening 50 accepted records and creating the 10 km / 50 km grid comparison. This is a local execution check, **not** successful Binder execution or Python 3.11 conda parity. All 50 accepted records originated from one source (iNaturalist); it is a source-biased non-random preview.

The inherited EDS Book workflow intentionally **skips** tests on personal-author repositories. A historical [GitHub Actions run #40365940396](https://github.com/saramjh/bird-records-not-absence-notebook/actions/runs/40365940396) separately passed 18 offline source and grid tests and executed all four notebook code cells on Ubuntu/Python 3.11. Those author-only CI jobs were then removed, and `.github/workflows/test.yaml` restored to the exact [EDS Book template in commit 0ed35d9](https://github.com/saramjh/bird-records-not-absence-notebook/commit/0ed35d9732fdf69ad5bdd7fe098ac4f0f97464cd) to comply with the [author guidelines](https://edsbook.org/guidelines-authors#preparation). These are historical test receipts, not current workflow coverage, Binder validation, a GBIF occurrence-download DOI or editorial acceptance.

## Frozen safe teaching snapshot

The file data/first-page-grids-20261026.json retains only counts per 10 km projected grid cell, screening exclusions, publisher datasets/DOIs, and the original query/retrieval time. It includes no individual observation IDs, species identities, observers, dates or precise point coordinates. Its 50 km cells are calculated from the same 10 km counts using a shared projected origin.

This is a non-random, source-biased, derived teaching aggregate; it is not a GBIF occurrence-download DOI or a biological range/absence result. Set LIVE_GBIF = True only if an opt-in current API example is specifically needed; current records and publisher credits require re-review. The default offline path allows a notebook runtime to be tested without relying on GBIF API uptime.

Run python -m unittest discover -p test_*.py for screening and snapshot integrity checks. Full notebook execution still needs the Python notebook dependencies. A separately versioned GBIF download DOI, geographic source-selection caveats and Binder provider validation remain open publication requirements.