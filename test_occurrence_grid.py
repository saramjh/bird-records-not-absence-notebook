import unittest
from occurrence_grid import screen,aggregate
def row(id,**kwargs):
    d={"gbifID":id,"license":"http://creativecommons.org/publicdomain/zero/1.0/legalcode","countryCode":"KR","country":"Korea, Republic of","basisOfRecord":"HUMAN_OBSERVATION","year":2024,"decimalLatitude":37.5,"decimalLongitude":127,"coordinateUncertaintyInMeters":500,"datasetKey":"publisher"}
    d.update(kwargs)
    return d
class QualityTests(unittest.TestCase):
    def test_missing_uncertainty_is_excluded(self):
        good,ex=screen([row(1,coordinateUncertaintyInMeters=None)])
        self.assertFalse(good)
        self.assertEqual(ex["uncertainty_missing"],1)
    def test_boundary_and_provenance(self):
        good,ex=screen([row(1,coordinateUncertaintyInMeters=1000)])
        self.assertEqual(good[0]["datasetKey"],"publisher")
        self.assertEqual(ex,{})
    def test_bad_license(self):
        good,ex=screen([row(1,license="https://creativecommons.org/licenses/by-nc/4.0/")])
        self.assertEqual(ex["not_cc0"],1)
    def test_duplicate(self):
        good,ex=screen([row(1),row(1)])
        self.assertEqual(len(good),1)
        self.assertEqual(ex["missing_or_duplicate_id"],1)
    def test_invalid_geo(self):
        good,ex=screen([row(1,decimalLatitude=100),row(2,year=2023)])
        self.assertFalse(good)
        self.assertEqual(ex["invalid_coordinate"],1)
        self.assertEqual(ex["outside_scope"],1)
    def test_grids_conserve_record_count_not_occupied_cells(self):
        p=[(499999,4100000),(510001,4100000),(520001,4100000)]
        a=aggregate(p,10000)
        b=aggregate(p,50000)
        self.assertEqual(sum(a.values()),3)
        self.assertEqual(sum(b.values()),3)
        self.assertNotEqual(len(a),len(b))
    def test_negative_floor(self):
        self.assertEqual(aggregate([(-1,-1)],10000),{(-1,-1):1})
if __name__=="__main__":
    unittest.main()
