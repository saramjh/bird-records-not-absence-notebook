# When a bird map looks empty

A preparation-stage Python notebook for Environmental Data Science Book idea [#14](https://github.com/eds-book/notebooks-ideas/issues/14), created from the [official Python template](https://github.com/eds-book/template_python).

**Author:** Jihun Oh. The question arose while developing [KoreAves](https://koreaves.com); KoreAves is a disclosed optional case study, NOT this notebook's original data provider. No EDS Book peer review, Binder validation or publication is claimed.

The notebook screens CC0-licensed records from a **bounded first page** of the live GBIF occurrence API, distinguishes missing coordinate uncertainty from zero uncertainty, compares 10 km and 50 km analyst-defined projected grids, and explains why record counts and blank cells do NOT establish bird abundance or absence.

This page of the live API is non-random, not versioned and may change. It is **not a completed data product**. Before review, replace it with a [DOI-versioned GBIF occurrence download](https://www.gbif.org/citation-guidelines), audit dataset publisher credits and licence, and test the final notebook through Binder. No third-party photos or sound recordings are distributed. Fine-scale occurrence coordinates are not stored in the repository.

## Run

Use the template's environment.yml with conda/mamba, open notebook.ipynb, and run all cells with an internet connection for the GBIF API. Non-network tests: python -m unittest discover -p 'test_*.py'.

Only the preparation branch carries this candidate notebook; template workflow files under .github/workflows have not been modified.
