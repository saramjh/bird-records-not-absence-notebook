# When a bird map looks empty

A preparation-stage Python notebook for Environmental Data Science Book idea [#14](https://github.com/eds-book/notebooks-ideas/issues/14), created from the [official Python template](https://github.com/eds-book/template_python).

**Author:** Jihun Oh. The question arose while developing [KoreAves](https://koreaves.com); KoreAves is a disclosed optional case study, NOT this notebook's original data provider. No EDS Book peer review, Binder validation or publication is claimed.

The notebook screens CC0-licensed records from a **bounded first page** of the live GBIF occurrence API, distinguishes missing coordinate uncertainty from zero uncertainty, compares 10 km and 50 km analyst-defined projected grids, and explains why record counts and blank cells do NOT establish bird abundance or absence.

This page of the live API is non-random, not versioned and may change. It is **not a completed data product**. Before review, replace it with a [DOI-versioned GBIF occurrence download](https://www.gbif.org/citation-guidelines), audit dataset publisher credits and licence, and test the final notebook through Binder. No third-party photos or sound recordings are distributed. Fine-scale occurrence coordinates are not stored in the repository.

## Run

Use the template's environment.yml with conda/mamba, open notebook.ipynb, and run all cells with an internet connection for the GBIF API. Non-network tests: python -m unittest discover -p 'test_*.py'.

Only the preparation branch carries this candidate notebook; template workflow files under .github/workflows have not been modified.

## Provenance, citation and execution QA (2026-10-26)

The GBIF query's first 100 individual-record CC0 occurrences contained 61 from [iNaturalist](https://doi.org/10.15468/ab3s5x) and 39 from [NSMK local biodiversity recordings](https://doi.org/10.15468/ya2fjz). The overall iNaturalist dataset licence is **CC BY-NC 4.0** while some individual records are CC0; photos and sounds must be licensed separately. These two DOIs identify the contributing **datasets**, not a stable GBIF occurrence **download** for the sampled query. No precise locations or imagery were added to this repository.

The notebook executed all four code cells on isolated Windows Python 3.13 (numpy 2.1.3, matplotlib 3.9.4, pyproj 3.7.1, nbclient 0.10.2), screening 50 accepted records and creating the 10 km / 50 km grid comparison. This is a local execution check, **not** successful Binder execution or Python 3.11 conda parity. All 50 accepted records originated from one source (iNaturalist); it is a source-biased non-random preview.

The inherited template GitHub Action test job was **skipped as designed** for personal repositories by its upstream eds-book ownership guard; that does not constitute CI test success.
