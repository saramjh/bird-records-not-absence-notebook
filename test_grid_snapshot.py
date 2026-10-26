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
