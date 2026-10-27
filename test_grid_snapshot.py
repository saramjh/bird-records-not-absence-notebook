import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy

from grid_snapshot import derive_grids, load_snapshot

SOURCE = Path(__file__).parent / "data" / "first-page-grids-20261026.json"

class AggregateSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.source=json.loads(SOURCE.read_text(encoding="utf8"))

    def _attempt(self,data):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"fixture.json"
            p.write_text(json.dumps(data),encoding="utf8")
            return load_snapshot(p)

    def test_reject_source_metadata_year_or_taxon_drift(self):
        for field, changed in (("query_year", 2023), ("query_taxon", "Mammalia"),
                               ("query_taxon_rank", "species")):
            d = deepcopy(self.source)
            d[field] = changed
            with self.subTest(field=field), self.assertRaisesRegex(
                ValueError, "changed scientific source selection"
            ):
                self._attempt(d)

    def test_reject_original_api_query_filter_or_paging_drift(self):
        url = self.source["original_api_query"]
        changes = (("year=2024", "year=2023"),
                   ("license=CC0_1_0", "license=CC_BY_4_0"),
                   ("offset=0", "offset=100"),
                   ("hasCoordinate=true", "hasCoordinate=false"))
        for original, altered in changes:
            d = deepcopy(self.source)
            d["original_api_query"] = url.replace(original, altered)
            with self.subTest(altered=altered), self.assertRaisesRegex(
                ValueError, "changed scientific source selection"
            ):
                self._attempt(d)

    def test_snapshot_integrity(self):
        d=load_snapshot(SOURCE)
        fine,coarse=derive_grids(d["cells_10km"])
        self.assertEqual(sum(fine.values()),50)
        self.assertEqual(sum(coarse.values()),50)
        self.assertEqual((len(fine),len(coarse)),(12,8))
        self.assertIsNone(d["GBIF_occurrence_download_doi"])

    def test_private_individual_occurrences_not_in_snapshot(self):
        text=SOURCE.read_text(encoding="utf8")
        for key in ('decimalLatitude','decimalLongitude','gbifID','scientificName','recordedBy','occurrenceID'):
            self.assertNotIn(key,text)

    def test_reject_grid_imbalance(self):
        d=deepcopy(self.source)
        d["cells_10km"][0][2]+=1
        with self.assertRaises(ValueError):
            self._attempt(d)

    def test_reject_missing_dataset_credit(self):
        d=deepcopy(self.source)
        d["dataset_dois"]={}
        with self.assertRaises(ValueError):
            self._attempt(d)

    def test_reject_more_accepted_than_source_dataset(self):
        d=deepcopy(self.source)
        source_with_39=next(k for k,v in d["first_page_dataset_counts"].items() if v==39)
        d["accepted_dataset_counts"]={source_with_39:d["accepted_count"]}
        with self.assertRaisesRegex(ValueError,"exceed source"):
            self._attempt(d)

    def test_reject_negative_dataset_source_with_balanced_total(self):
        d=deepcopy(self.source)
        keys=list(d["first_page_dataset_counts"])
        d["first_page_dataset_counts"]={keys[0]:120,keys[1]:-20}
        with self.assertRaisesRegex(ValueError,"invalid dataset record count"):
            self._attempt(d)

    def test_reject_invalid_dataset_doi(self):
        d=deepcopy(self.source)
        key=next(iter(d["dataset_dois"]))
        d["dataset_dois"][key]="not-a-dataset-doi"
        with self.assertRaisesRegex(ValueError,"invalid dataset citation DOI"):
            self._attempt(d)

    def test_reject_boolean_dataset_count(self):
        d=deepcopy(self.source)
        key=next(iter(d["accepted_dataset_counts"]))
        d["accepted_dataset_counts"][key]=True
        with self.assertRaises(ValueError):
            self._attempt(d)

    def test_reject_duplicate_cells(self):
        d=deepcopy(self.source)
        d["cells_10km"].append(d["cells_10km"][0])
        with self.assertRaises(ValueError):
            self._attempt(d)

    def test_negative_origin_floor(self):
        fine,coarse=derive_grids([[-1,-1,2],[0,0,3]])
        self.assertEqual(coarse,{(-1,-1):2,(0,0):3})

    def test_bad_schema(self):
        d=deepcopy(self.source)
        d["schema"]="UNKNOWN"
        with self.assertRaises(ValueError):
            self._attempt(d)

if __name__=="__main__":
    unittest.main()
