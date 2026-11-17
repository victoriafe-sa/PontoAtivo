import json, unittest
from pathlib import Path

class PrivadosTest(unittest.TestCase):
    def test_private_catalog_has_official_source_without_accessibility_inference(self):
        places=json.loads((Path(__file__).parents[2]/"data"/"curadoria"/"privados.json").read_text())
        self.assertGreaterEqual(len(places),4)
        for place in places:
            self.assertEqual(place["ownership"],"private")
            self.assertTrue(place["address"] and place["source_url"] and place["modalities"])
            self.assertNotEqual(place.get("evidence",{}).get("accessible_pool",{}).get("level"),"campo")
            self.assertIn(place["access_rule"],("members","contact","unknown","day_use"))

if __name__ == "__main__": unittest.main()
