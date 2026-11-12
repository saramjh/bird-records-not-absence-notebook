# When a bird map looks empty

A preparation-stage Python notebook for Environmental Data Science Book idea [#14](https://github.com/eds-book/notebooks-ideas/issues/14), created from the [official Python template](https://github.com/eds-book/template_python).

**Author:** Jihun Oh. The question arose while developing [KoreAves](https://koreaves.com); KoreAves is a disclosed optional case study, NOT this notebook's original data provider. No EDS Book peer review or publication is claimed.

The notebook screens CC0-licensed records from a **bounded first page** of the live GBIF occurrence API, distinguishes missing coordinate uncertainty from zero uncertainty, compares 10 km and 50 km analyst-defined projected grids, and explains why record counts and blank cells do NOT establish bird abundance or absence.

This page of the live API is non-random, not versioned and may change. It is **not a completed data product**. Before review, replace it with a [DOI-versioned GBIF occurrence download](https://www.gbif.org/citation-guidelines), audit dataset publisher credits and licence, and test the final notebook through Binder. No third-party photos or sound recordings are distributed. Fine-scale occurrence coordinates are not stored in the repository.

## Two-minute reader exercise: what does an empty bird map tell us?

Imagine you find a blank square on a map of South Korean bird records. Before treating it as evidence that no bird was present, check three things:

1. **Which records were searched?** This example queries GBIF for 2024 human-observation records in South Korea, restricted to CC0 occurrences with coordinates and no flagged geospatial issue. It does not search every source or every year.
2. **Which records survived the screen?** On 11 November 2026, a read-only check of the entire mutable search returned 5,519 rows. Of those, 5,208 lacked a reported coordinate-uncertainty value, 36 reported more than 1,000 m, and 275 passed the example's screen. All 275 came from one contributing dataset. The 1,000 m threshold is a teaching choice, not a standard for declaring an observation reliable.
3. **How was the map drawn?** The separate **first-100-row teaching snapshot** kept 50 records and placed them in 12 occupied 10 km grid cells or 8 occupied 50 km cells. The cell size changes what looks occupied. These figures are from the small historical snapshot, **not** a map of the 275 passing records from the full search.

**Question for a reader:** If a cell is blank, can we conclude that birds were absent? **No.** At most, this example says that no qualifying source record was drawn in that cell under these particular filters. It says nothing about whether anyone searched there, how thoroughly they looked, or whether they would have detected a bird.

The [GET-only whole-query audit](audit_live_gbif_search.py) reports aggregate results without exporting precise coordinates or observer details. Its results can change as GBIF's search index changes; a versioned occurrence-download DOI is still needed for a reproducible published analysis. This is an author-owned learning aid, not an EDS Book-reviewed chapter or a biological survey.


## Run

Use the template's environment.yml with conda/mamba, open notebook.ipynb, and run all cells offline using the bundled derived grid snapshot (LIVE_GBIF = False). Non-network tests: python -m unittest discover -p 'test_*.py'.

Only the `preparation` branch carries this candidate notebook. On 4 November 2026, [commit `a9905b5`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/a9905b56fde114abe3586f4385b9d457028fbb8b) restored `.github/workflows/test.yaml` **exactly to the original EDS Book template** (matching the `main` branch's blob). The additional author-side test job from 27 October was removed to comply with [EDS Book's author guidelines](https://edsbook.org/guidelines-authors#preparation), which reserve workflow edits for the Editor-in-Chief. The inherited EDS Book build job remains gated to `eds-book` organization repositories. Run author-side tests locally instead of modifying the template workflow.

## Provenance, citation and initial local QA (26 October 2026)

The GBIF query's first 100 individual-record CC0 occurrences contained 61 from [iNaturalist](https://doi.org/10.15468/ab3s5x) and 39 from [NSMK local biodiversity recordings](https://doi.org/10.15468/ya2fjz). The overall iNaturalist dataset licence is **CC BY-NC 4.0** while some individual records are CC0; photos and sounds must be licensed separately. These two DOIs identify the contributing **datasets**, not a stable GBIF occurrence **download** for the sampled query. No precise locations or imagery were added to this repository.

The notebook executed all four code cells on isolated Windows Python 3.13 (numpy 2.1.3, matplotlib 3.9.4, pyproj 3.7.1, nbclient 0.10.2), screening 50 accepted records and creating the 10 km / 50 km grid comparison. At that point, the local check alone did **not** establish Binder or Python 3.11 conda parity; a separate successful 27 October live Binder run is documented below. All 50 accepted records originated from one source (iNaturalist), so the preview remains source-biased and non-random.

The inherited EDS Book **reusable build job** intentionally **skips** non-`eds-book` repositories. Before the template was restored, historical author-side [GitHub Actions run #40365940396](https://github.com/saramjh/bird-records-not-absence-notebook/actions/runs/40365940396) passed 18 offline tests and executed all four notebook code cells on Ubuntu/Python 3.11, and [run #40488442826](https://github.com/saramjh/bird-records-not-absence-notebook/actions/runs/40488442826) reported 28 offline tests passed. These are **historical CI results, not checks on the present PR head**. On 4 November 2026, commit `a9905b5` restored the original EDS Book workflow; a fresh, isolated Windows checkout of that exact commit independently passed **28/28 local non-network tests** with `python -m unittest discover -p 'test_*.py' -v`. This does not establish a publication build, a new live Binder run, a GBIF occurrence-download DOI, editorial acceptance or research adoption.

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

### Recheck of the existing NSMK CC0 download (11 November 2026)

The historical [GBIF occurrence download 10.15468/dl.u7tcq5](https://doi.org/10.15468/dl.u7tcq5) is a fixed 3,359-record archive from the National Science Museum of Korea's [bird observations dataset](https://doi.org/10.15468/ya2fjz). The archive rights and all occurrence licences are CC0. Its SHA-256 is 9ed28c2cfb96d83a0f0bdcba90598474efc1f34f675619c049da308ffce8c098.

An offline recheck found 3,207 records dated 2024, all marked as human observations in South Korea, with coordinates and without reported geospatial issues. All 3,207 lack a reported coordinate-uncertainty value. The current notebook excludes missing uncertainty, so **zero** records from this archive pass that existing screen. Coordinate fields do not establish location precision.

Run the read-only audit using a locally downloaded copy of the original GBIF DwC-A ZIP:

    python audit_existing_gbif_doi.py path/to/original-download.zip

The auditor checks the archive hash, dataset citation and source licences using only the Python standard library. It prints aggregate counts without exporting individual coordinates, observer details or IDs. No GBIF account or new download request is used. The original archive is **not** committed.

### Check a future full-result download DOI (GET only)

After a GBIF account holder obtains a new DOI for the exact full query, run `python verify_download_doi.py --doi 10.15468/dl.YOURKEY`. The checker retrieves GBIF's public download metadata and compares the complete source predicates, the historical Backbone checklist key, the DwC-A format and the CC0 licence with this notebook's frozen query settings. It uses an unauthenticated GET and does not request a new download. If the DOI belongs to a different selection, the check fails. The historical NSMK DOI `10.15468/dl.u7tcq5` fails because its source predicate and checklist do not match.

A metadata match alone does not verify the ZIP hash, publisher credits or record-level rights. Before replacing any figure, audit the returned download archive, rebuild the derived grid and recheck the notebook runtime. This author-owned PR remains in Draft.

### Turn a verified DOI archive into a private grid candidate

Once the owner has a matching full-query download DOI and its original ZIP, the optional `gbif_doi_grid_candidate.py` script checks the DOI metadata, ZIP size and SHA-256, source rights, per-record selection and observation status. It produces 10 km and 50 km aggregate counts without exporting the underlying observation IDs or coordinates.

Example: `python gbif_doi_grid_candidate.py --doi 10.15468/dl.YOURKEY --archive original.zip --sha256 YOUR_VERIFIED_64_HEX_SHA --output candidate.json`

The script refuses to overwrite an existing output. A candidate needs separate publisher attribution and record-rights review, the notebook's figure rebuild, and a fresh Binder test before any publication decision. The sample maps currently in the notebook remain unchanged.

### Original archive and occurrence-status recheck (12 November 2026)

The [existing GBIF download](https://api.gbif.org/v1/occurrence/download/10.15468/dl.u7tcq5) was retrieved using its published key `0015299-260903145123482`. The 497,529-byte DwC-A ZIP matched SHA-256 `9ed28c2cfb96d83a0f0bdcba90598474efc1f34f675619c049da308ffce8c098`. Its interpreted `occurrence.txt` has 230 columns, including `occurrenceStatus`; all 3,359 records report `PRESENT`.

The revised archive auditor now requires that status column and excludes `NOT_DETECTED`, `ABSENT` and unknown statuses from accepted records. On this original ZIP it returned 3,207 records for 2024, zero exclusions for occurrence status, and 3,207 missing reported coordinate-uncertainty values. No records passed the example's 1,000 m threshold. The archive was used in a temporary directory and was not committed. The status check also passed synthetic regression tests; the full remote `preparation` branch passed 56 offline tests at commit [`9c3c767`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/9c3c7672b44ba244eb0de3285a0609fcb8a8f49b). These checks do not create a selection-specific download DOI.

This NSMK-only archive does not match the notebook's earlier nonrandom first-100-record sample that mixed providers. The existing first-page figure and notebook input are unchanged. Replacing them would require a separately justified screening decision, fresh figures and runtime tests. The EDS Book draft remains unsubmitted for editorial review.

### Whole-query read-only check (11 November 2026)

A separate, opt-in GET-only audit of the [original GBIF occurrence search](https://api.gbif.org/v1/occurrence/search?country=KR&taxonKey=212&basisOfRecord=HUMAN_OBSERVATION&year=2024&license=CC0_1_0&hasCoordinate=true&hasGeospatialIssue=false&limit=300&offset=0) inspected all 5,519 returned records across 19 pages between 10:41 and 10:42 UTC on 11 November 2026. Applying the notebook's original occurrence_grid.screen 1,000m criterion to the entire result excluded 5,208 records with missing reported coordinate uncertainty and 36 above the illustrative threshold. **275 records passed**, all from one iNaturalist dataset key (50c9509d-22c7-4a22-a47d-8c48425ef4a7). The search involves six contributing dataset keys in total.

Run 'python audit_live_gbif_search.py' only when explicitly opting in to a fresh public API scan. The synthetic-only tests do not make network requests. The audit prints aggregate counts and provider keys without storing occurrence IDs, coordinates, observer names or attachments.

These are **current search-index records, not a frozen GBIF download**. The API total was consistent across pages, but that does not guarantee a single immutable snapshot; later queries can differ. The original first-page grid exercise is unchanged. Even with full-query screening, every accepted record came from one provider, so neither the 275 accepted records nor the map can establish abundance or absence. A selection-specific versioned download DOI and final figure/runtime validation remain necessary before editorial submission.

### Occurrence-status guard (11 November 2026)

GBIF [normalizes older PRESENT/ABSENT values to DETECTED/NOT_DETECTED](https://gbif.github.io/gbif-api/apidocs/org/gbif/api/vocabulary/OccurrenceStatus.html). The screening code now accepts reported DETECTED or legacy PRESENT records and excludes NOT_DETECTED, ABSENT, or unrecognized/missing status. A surveyed non-detection must not be counted as a bird sighting. This does not turn an empty map cell into a surveyed absence.

A read-only GBIF occurrence-status facet of the same 2024 South Korea search reported all 5,519 indexed records as DETECTED on 11 November 2026. The status guard therefore does not change the 275 qualifying records in that observed query. It protects future scans if the underlying indexed data or API status values change. These are still mutable search records, not a versioned GBIF occurrence download.

### Offline notebook runtime checks (11 November 2026)

The original notebook was executed from the existing preparation branch in isolated Windows Python 3.13.1 and Python 3.11.17 environments. Both ran all four code cells with LIVE_GBIF set to False against the bundled aggregate snapshot. Each reported 50 accepted records from the historical first 100 GBIF search results, with 12 occupied 10 km cells and 8 occupied 50 km cells. Both rendered a 1052 by 577 pixel PNG with identical SHA-256 (2164acd8b8c90f7b1c702f5f0d08b3395fee02a34c6c18eaaf5f6e4bf4d462a5).

The Python 3.11.17 check used NumPy 2.1.3, Matplotlib 3.9.4 and pyproj 3.7.2. The full 54-test suite also passed on that interpreter. The same notebook was previously tested on Python 3.13.1 with NumPy 2.1.3, Matplotlib 3.9.4 and pyproj 3.7.1. Both were offline runs; no new GBIF download or observation-level export occurred.

These tests establish local Python 3.11 compatibility with the declared package families. The actual conda build and the current commit on the remote Binder service have not been verified. The original notebook, aggregate snapshot and map source remain unchanged, and the first-page records still lack a versioned occurrence-download DOI.

### Preparation-head offline check (13 November 2026)

At commit [`6309308`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/6309308e599c3a6b19e38f4444789d737509014c), the author-owned `preparation` branch passed all **77 non-network unit tests** with Windows Python 3.11.17. The notebook's four original code cells also ran offline in one Python process, using the existing aggregate snapshot. The 50 screened records occupied 12 cells at 10 km resolution and 8 cells at 50 km. The resulting PNG matched the earlier local figure SHA-256: `2164acd8b8c90f7b1c702f5f0d08b3395fee02a34c6c18eaaf5f6e4bf4d462a5`.

A separate Jupyter-kernel run on the same head could not complete because the Windows process hit `RESOURCE_EXCEEDED`. The successful single-process check establishes offline cell execution; it is not a fresh Binder run, a Jupyter-kernel check, or proof of a versioned GBIF dataset. The sample remains non-random and source-biased. A matching occurrence-download DOI, source-rights audit, rebuilt figures and final Binder test are still needed before editorial review is requested.

## Frozen safe teaching snapshot

**Aggregate-data guard (4 November 2026):** The author-owned `grid_snapshot.load_snapshot` rejects unexpected top-level fields and rejects record-level occurrence IDs, coordinates, observer names and species fields even when nested. A synthetic-only regression test reproduced the prior acceptance of an unreviewed raw record and verifies that it is now rejected. After the initial [31-test regression commit `8f25157`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/8f25157841f1def81edd5e8f0a2948819662a3cf), [commit `dde748e`](https://github.com/saramjh/bird-records-not-absence-notebook/commit/dde748e5871020da301b8eb2ded1bc4a10118eb9) further restricted the `limitations` array to nonempty explanatory strings, rejecting arbitrary nested metadata. Its exact remote head passed **33/33 offline tests** on a fresh checkout. This is a guard against accidental inclusion, not proof that the historical sample is representative, DOI-frozen, independently reviewed or publication-ready.

The file data/first-page-grids-20261026.json retains only counts per 10 km projected grid cell, screening exclusions, publisher datasets/DOIs, and the original query/retrieval time. It includes no individual observation IDs, species identities, observers, dates or precise point coordinates. Its 50 km cells are calculated from the same 10 km counts using a shared projected origin.

This is a non-random, source-biased, derived teaching aggregate; it is not a GBIF occurrence-download DOI or a biological range/absence result. Set LIVE_GBIF = True only if an opt-in current API example is specifically needed; current records and publisher credits require re-review. The default offline path allows a notebook runtime to be tested without relying on GBIF API uptime.

Run python -m unittest discover -p test_*.py for screening and snapshot integrity checks. Independent local full-notebook runs require the Python dependencies in the template environment. The live Binder run below verified the offline teaching path on 27 October; a separately versioned GBIF occurrence-download DOI, geographic source-selection review and publication-build QA remain open.

## Verified Binder runtime (27 October 2026)

Binder executed all four code cells from [commit 3ae6a75](https://github.com/saramjh/bird-records-not-absence-notebook/commit/3ae6a7594b1544d71bf38add6100983722b8d749) successfully in one authenticated run, observed 02:35–02:37 UTC. Each cell returned `ok`, including the final Matplotlib figure. The actual PNG was inspected after the colorbar-overlap and dark-cell label-contrast fixes. The offline aggregate still contains 50 screened records, with 12 occupied 10 km cells and 8 occupied 50 km cells. The kernel was deleted after verification.

This verifies the default offline teaching path and corrected figure rendering. It is not a DOI-backed GBIF data reproduction, publication-build validation, peer review, editorial acceptance or research adoption. The earlier CI receipts above remain separate from this Binder runtime check.
