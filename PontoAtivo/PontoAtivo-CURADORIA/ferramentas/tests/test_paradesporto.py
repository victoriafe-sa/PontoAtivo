import json, unittest
from pathlib import Path

class ParadesportoTest(unittest.TestCase):
    def test_institutional_places_and_unconfirmed_entities(self):
        base=Path(__file__).parents[2]/"data"/"curadoria"
        places=json.loads((base/"paradesporto.json").read_text())
        review=json.loads((base/"revisao.json").read_text())
        cetefe=next(p for p in places if p["id"]=="para-cetefe")
        self.assertEqual(cetefe["evidence"]["address"]["level"], "organizacao")
        self.assertTrue(all(m.get("evidence") for p in places for m in p["modalities"]))
        self.assertTrue(any(x["entity"]=="UNIACE" and x["reason"]=="regular_training_address_unconfirmed" for x in review))
        self.assertTrue(all("personal_contact" not in p for p in places))

if __name__ == "__main__": unittest.main()
