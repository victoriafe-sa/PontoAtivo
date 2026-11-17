import unittest
from ferramentas.importar_ibram import match_pending_parks, normalize_park_name, point_in_geometry, representative_point


class IbramTest(unittest.TestCase):
    def test_aliases_and_accents(self):
        self.assertEqual(normalize_park_name("Parque Irmão Afonso Haus"), normalize_park_name("Parque Irmãos Afonso Haus"))
        self.assertEqual(normalize_park_name("Cachoeirinha e Coqueirão"), normalize_park_name("Cachoeirinha"))

    def test_representative_point_stays_inside_concave_polygon(self):
        geometry = {"rings":[[[-48.10,-15.80],[-48.06,-15.80],[-48.06,-15.79],[-48.09,-15.79],[-48.09,-15.76],[-48.10,-15.76],[-48.10,-15.80]]]}
        lon, lat = representative_point(geometry)
        self.assertTrue(point_in_geometry(lon, lat, geometry))

    def test_matching_reports_unmatched(self):
        pending = [{"id":"a","name":"Parque Cachoeirinha"},{"id":"b","name":"Parque Inexistente"}]
        features = [{"attributes":{"nome":"Parque Cachoeirinha e Coqueirão"},"geometry":{"rings":[[[-48,-15.8],[-47.9,-15.8],[-47.9,-15.7],[-48,-15.7],[-48,-15.8]]]}}]
        report = match_pending_parks(pending, features)
        self.assertEqual(len(report["matched"]), 1)
        self.assertEqual(report["unmatched"], ["b"])


if __name__ == "__main__": unittest.main()
