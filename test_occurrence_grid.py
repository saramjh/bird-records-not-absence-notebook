import unittest
from occurrence_grid import screen,aggregate
def row(id,**kwargs):
    d={"gbifID":id,"license":"http://creativecommons.org/publicdomain/zero/1.0/legalcode","countryCode":"KR","country":"Korea, Republic of","basisOfRecord":"HUMAN_OBSERVATION","year":2024,"decimalLatitude":37.5,"decimalLongitude":127,"coordinateUncertaintyInMeters":500,"datasetKey":"publisher","occurrenceStatus":"DETECTED"}
    d.update(kwargs)
    return d
class QualityTests(unittest.TestCase):
    def test_detected_and_legacy_present_are_screened_normally(self):
        good, excluded = screen([row(1, occurrenceStatus="DETECTED"),
                                 row(2, occurrenceStatus="PRESENT")])
        self.assertEqual(len(good), 2)
        self.assertEqual(excluded, {})

    def test_survey_nondetections_are_never_counted_as_sightings(self):
        good, excluded = screen([row(1, occurrenceStatus="NOT_DETECTED"),
                                 row(2, occurrenceStatus="ABSENT")])
        self.assertEqual(good, [])
        self.assertEqual(excluded, {"not_detected": 2})

    def test_unknown_or_missing_status_does_not_imply_detection(self):
        good, excluded = screen([row(1, occurrenceStatus=None),
                                 row(2, occurrenceStatus=""),
                                 row(3, occurrenceStatus="UNCLASSIFIED")])
        self.assertEqual(good, [])
        self.assertEqual(excluded, {"unknown_occurrence_status": 3})

    def test_missing_uncertainty_is_excluded(self):
        good,ex=screen([row(1,coordinateUncertaintyInMeters=None)])
        self.assertFalse(good)
        self.assertEqual(ex["uncertainty_missing"],1)
    def test_zero_uncertainty_not_a_valid_accuracy_measure(self):
        # GBIF recommends blank/NULL for unknown precision; zero does not mean exact.
        data = [row(1, coordinateUncertaintyInMeters=0),
                row(2, coordinateUncertaintyInMeters="0"),
                row(3, coordinateUncertaintyInMeters=-1),
                row(4, coordinateUncertaintyInMeters=1)]
        accepted, excluded = screen(data)
        self.assertEqual([x["id"] for x in accepted], ["4"])
        self.assertEqual(excluded, {"uncertainty_invalid": 3})

    def test_boundary_and_provenance(self):
        good,ex=screen([row(1,coordinateUncertaintyInMeters=1000)])
        self.assertEqual(good[0]["datasetKey"],"publisher")
        self.assertEqual(ex,{})
    def test_cc0_license_is_only_accepted_at_official_url(self):
        deceptive = [
            "https://example.org/notes?other=https://creativecommons.org/publicdomain/zero/1.0/legalcode",
            "https://creativecommons.org.evil.example/publicdomain/zero/1.0/legalcode",
            "https://creativecommons.org/publicdomain/zero/1.0-not-the-deed",
            "https://creativecommons.org/licenses/by/4.0/?cc0=https://creativecommons.org/publicdomain/zero/1.0/",
            "https://creativecommons.org/publicdomain/zero/1.0/legalcode?tracking=unverified",
        ]
        ok, excluded = screen([row(i + 1, license=lic) for i, lic in enumerate(deceptive)])
        self.assertEqual(ok, [])
        self.assertEqual(excluded["not_cc0"], len(deceptive))

    def test_cc0_official_urls_retained(self):
        valid = [
            "https://creativecommons.org/publicdomain/zero/1.0/",
            "http://creativecommons.org/publicdomain/zero/1.0/legalcode",
            "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
        ]
        ok, rejected = screen([row(i + 1, license=lic) for i, lic in enumerate(valid)])
        self.assertEqual(len(ok), len(valid))
        self.assertEqual(rejected, {})

    def test_bad_license(self):
        good,ex=screen([row(1,license="https://creativecommons.org/licenses/by-nc/4.0/")])
        self.assertEqual(ex["not_cc0"],1)
    def test_duplicate(self):
        good,ex=screen([row(1),row(1)])
        self.assertEqual(len(good),1)
        self.assertEqual(ex["missing_or_duplicate_id"],1)
    def test_invalid_or_fractional_year_is_excluded_without_crashing(self):
        records = [
            row(1, year="not-a-year"),
            row(2, year=2024.9),
            row(3, year="2024.9"),
            row(4, year=None),
            row(5, year="2024"),
            row(6, year=2024),
        ]
        good, exclusions = screen(records)
        self.assertEqual([g["id"] for g in good], ["5", "6"])
        self.assertEqual(exclusions["outside_scope"], 4)

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
