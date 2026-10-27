# When a bird map looks empty

A preparation-stage Python notebook for Environmental Data Science Book idea [#14](https://github.com/eds-book/notebooks-ideas/issues/14), created from the [official Python template](https://github.com/eds-book/template_python).

**Author:** Jihun Oh. The question arose while developing [KoreAves](https://koreaves.com); KoreAves is a disclosed optional case study, NOT this notebook's original data provider. No EDS Book peer review or publication is claimed.

The notebook screens CC0-licensed records from a **bounded first page** of the live GBIF occurrence API, distinguishes missing coordinate uncertainty from zero uncertainty, compares 10 km and 50 km analyst-defined projected grids, and explains why record counts and blank cells do NOT establish bird abundance or absence.

This page of the live API is non-random, not versioned and may change. It is **not a completed data product**. Before review, replace it with a [DOI-versioned GBIF occurrence download](https://www.gbif.org/citation-guidelines), audit dataset publisher credits and licence, and test the final notebook through Binder. No third-party photos or sound recordings are distributed. Fine-scale occurrence coordinates are not stored in the repository.

## Run

Use the template's environment.yml with conda/mamba, open notebook.ipynb, and run all cells offline using the bundled derived grid snapshot (LIVE_GBIF = False). Non-network tests: python -m unittest discover -p 'test_*.py'.

Only the `preparation` branch carries this candidate notebook. The template workflow was restored to its upstream version at [`0ed35d9`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/0ed35d9732fdf69ad5bdd7fe098ac4f0f97464cd), but that is **historical**, not the current workflow state. On 27 October, [`73e93e1`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/73e93e1692cee657da1a46c2690c6bc228ba9257) added a separate owner-side pull-request test job. The inherited EDS Book build job remains gated to `eds-book` organization repositories.

## Provenance, citation and initial local QA (26 October 2026)

The GBIF query's first 100 individual-record CC0 occurrences contained 61 from [iNaturalist](https://doi.org/10.15468/ab3s5x) and 39 from [NSMK local biodiversity recordings](https://doi.org/10.15468/ya2fjz). The overall iNaturalist dataset licence is **CC BY-NC 4.0** while some individual records are CC0; photos and sounds must be licensed separately. These two DOIs identify the contributing **datasets**, not a stable GBIF occurrence **download** for the sampled query. No precise locations or imagery were added to this repository.

The notebook executed all four code cells on isolated Windows Python 3.13 (numpy 2.1.3, matplotlib 3.9.4, pyproj 3.7.1, nbclient 0.10.2), screening 50 accepted records and creating the 10 km / 50 km grid comparison. At that point, the local check alone did **not** establish Binder or Python 3.11 conda parity; a separate successful 27 October live Binder run is documented below. All 50 accepted records originated from one source (iNaturalist), so the preview remains source-biased and non-random.

The inherited EDS Book **reusable build job** intentionally **skips** non-`eds-book` repositories. A historical [GitHub Actions run #40365940396](https://github.com/saramjh/bird-records-not-absence-notebook/actions/runs/40365940396) separately passed 18 offline source and grid tests and executed all four notebook code cells on Ubuntu/Python 3.11. The initial extra jobs were removed and the template restored at commit `0ed35d9`; that was later superseded by a narrower author-side PR check. A separate owner-side PR job now runs the five offline GBIF provenance/no-send tests: in [GitHub Actions run #40482375730](https://github.com/saramjh/bird-records-not-absence-notebook/actions/runs/40482375730), **GBIF provenance - standalone offline tests** succeeded while the inherited `test-build` job was **skipped**. This is actual current author-run PR CI, **not** a rerun of the full 18-test suite, an EDS Book publication build, a GBIF occurrence-download DOI, editorial acceptance or research adoption.

## Historical GBIF downloads are not a DOI for this selection

Two legitimate GBIF occurrence downloads created for earlier **KoreAves** source work on 13 September 2026 should not be confused with the first-page teaching sample:

- [10.15468/dl.sp8k2g](https://doi.org/10.15468/dl.sp8k2g): 2,298,104 records; an all-years, all-licences South Korea bird/PRESENT selection using Catalogue of Life Aves. It does not have this notebook's `year=2024`, `license=CC0_1_0` or `basisOfRecord=HUMAN_OBSERVATION` filters.
- [10.15468/dl.u7tcq5](https://doi.org/10.15468/dl.u7tcq5): 3,359 records from one NSMK source dataset. It is likewise not this notebook's first-page selection.

These are **real download DOIs but are not the DOI for the 26 October 2026 illustrative snapshot**. The original GBIF search reported 5,519 matching records and this notebook retained only its mutable first 100 rows (50 accepted after screening). Creating a new DOI for the *complete* filtered download would identify that full versioned selection, **not retrospectively freeze the old first page**. A citable revision must rebuild the teaching aggregate from the actual DOI-versioned download, document the included records and publisher credit, and repeat figure/runtime checks. No such revision or matching download DOI is claimed here. See [GBIF download and citation requirements](https://www.gbif.org/citation-guidelines).

### Preparing a reproducible GBIF download (no send)

`gbif_download_request.py` generates an **offline request body** for a **new full-result** `DWCA` occurrence download with the original teaching sample's country, taxon, 2024, human-observation, CC0 and geospatial filters. It explicitly pins the historical **GBIF Backbone** taxonomy (`d7dddbf4-2cf0-4f39-9b2a-bb099caae36c`), because the original `taxonKey=212` used that scheme and a different checklist could change the result.

```sh
python gbif_download_request.py --email your-registered-gbif-email@example.org --output gbif-query-local.json
python -m unittest discover -p 'test_*.py'
```

**No request is sent, no account credentials are read, and no DOI is created by this script.** Its output is a prospective download request requiring a separately authorized GBIF account holder to submit; the entire download will differ from the old first-100-row sample. Once GBIF returns an actual download key and DOI, rebuild the aggregate from that versioned archive, recheck publisher/record rights and counts, and rerun notebook/runtime tests. Do not copy the old first-page figure or attach either historical KoreAves DOI as the new source. See [GBIF API download instructions](https://techdocs.gbif.org/en/data-use/api-downloads).

## Frozen safe teaching snapshot

The file data/first-page-grids-20261026.json retains only counts per 10 km projected grid cell, screening exclusions, publisher datasets/DOIs, and the original query/retrieval time. It includes no individual observation IDs, species identities, observers, dates or precise point coordinates. Its 50 km cells are calculated from the same 10 km counts using a shared projected origin.

This is a non-random, source-biased, derived teaching aggregate; it is not a GBIF occurrence-download DOI or a biological range/absence result. Set LIVE_GBIF = True only if an opt-in current API example is specifically needed; current records and publisher credits require re-review. The default offline path allows a notebook runtime to be tested without relying on GBIF API uptime.

Run python -m unittest discover -p test_*.py for screening and snapshot integrity checks. Independent local full-notebook runs require the Python dependencies in the template environment. The live Binder run below verified the offline teaching path on 27 October; a separately versioned GBIF occurrence-download DOI, geographic source-selection review and publication-build QA remain open.

## Verified Binder runtime (27 October 2026)

Binder executed all four code cells from [commit 3ae6a75](https://github.com/saramjh/bird-records-not-absence-notebook/commit/3ae6a7594b1544d71bf38add6100983722b8d749) successfully in one authenticated run, observed 02:35–02:37 UTC. Each cell returned `ok`, including the final Matplotlib figure. The actual PNG was inspected after the colorbar-overlap and dark-cell label-contrast fixes. The offline aggregate still contains 50 screened records, with 12 occupied 10 km cells and 8 occupied 50 km cells. The kernel was deleted after verification.

This verifies the default offline teaching path and corrected figure rendering. It is not a DOI-backed GBIF data reproduction, publication-build validation, peer review, editorial acceptance or research adoption. The earlier CI receipts above remain separate from this Binder runtime check.
