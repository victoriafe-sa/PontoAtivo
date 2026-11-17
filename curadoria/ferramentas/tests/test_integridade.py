"""Integridade dos arquivos curados (correções das etapas 1–5 após o diagnóstico de 10/11/2026)."""
import json
import unittest
from datetime import date
from pathlib import Path

from ferramentas.curadoria import validate_place

BASE = Path(__file__).parents[2] / "data" / "curadoria"


def load(name):
    return json.loads((BASE / name).read_text())


SOURCES = {s["id"]: s for s in load("fontes.json")}
TODAY = date(2026, 11, 10)


def as_place(record):
    return {**record, "latitude": record.get("latitude"), "longitude": record.get("longitude")}


class CuratedEvidenceTest(unittest.TestCase):
    def test_every_curated_place_validates_without_errors(self):
        for name in ("privados.json", "paradesporto.json"):
            for place in load(name):
                errors = [i for i in validate_place(as_place(place), SOURCES, TODAY) if i.severity == "error"]
                self.assertEqual(errors, [], f"{place['id']}: {errors}")

    def test_address_and_coordinates_are_separate_attributes(self):
        for name in ("privados.json", "paradesporto.json"):
            for place in load(name):
                ev = place["evidence"]
                self.assertIn("address", ev, place["id"])
                self.assertIn("coordinates", ev, place["id"])
                self.assertNotIn("location", ev, place["id"])

    def test_coordinates_without_documented_provenance_are_not_published(self):
        for name in ("privados.json", "paradesporto.json"):
            for place in load(name):
                coords = place["evidence"]["coordinates"]
                if place.get("latitude") is not None:
                    self.assertNotEqual(coords["level"], "desconhecido", place["id"])
                    self.assertTrue(coords.get("source_id"), place["id"])
                else:
                    self.assertEqual(coords["level"], "desconhecido", place["id"])

    def test_private_evidence_points_to_registered_source_with_dates(self):
        for place in load("privados.json"):
            for field, ev in place["evidence"].items():
                if ev["level"] == "desconhecido":
                    continue
                self.assertIn(ev.get("source_id"), SOURCES, f"{place['id']}.{field}")
                self.assertTrue(ev.get("checked_at"), f"{place['id']}.{field}")
                self.assertTrue(ev.get("source_date") or ev.get("source_date_unknown"), f"{place['id']}.{field}")

    def test_accessibility_stays_unknown_without_evidence(self):
        for name in ("privados.json", "paradesporto.json"):
            for place in load(name):
                acc = place["evidence"].get("accessibility", {"level": "desconhecido"})
                self.assertEqual(acc["level"], "desconhecido", place["id"])

    def test_no_placeholder_cpb_date_without_document(self):
        for place in load("paradesporto.json"):
            for mod in place["modalities"]:
                ev = mod["evidence"]
                if ev["source_id"] == "cpb":
                    self.assertTrue(ev.get("source_date_unknown"), f"{place['id']}/{mod['name']}")
                    self.assertFalse(ev.get("source_date"), f"{place['id']}/{mod['name']}")


class ReviewQueueTest(unittest.TestCase):
    def setUp(self):
        self.review = load("revisao.json")
        self.by_place = {}
        for item in self.review:
            self.by_place.setdefault(item.get("place_id"), []).append(item)

    def test_review_ids_are_unique(self):
        ids = [item["id"] for item in self.review]
        self.assertEqual(len(ids), len(set(ids)))

    def test_removed_coordinates_are_traceable(self):
        expected = {"para-cetefe", "para-diref", "para-escola-fatima", "priv-clube-naval", "priv-aabb", "priv-minas", "priv-aeronautica"}
        found = {i["place_id"] for i in self.review if i["reason"] == "coordinates_provenance_undocumented"}
        self.assertEqual(found, expected)

    def test_possible_duplicates_are_registered(self):
        reasons = {(i.get("place_id"), i["reason"]) for i in self.review}
        self.assertIn(("para-escola-fatima", "possible_duplicate"), reasons)
        self.assertIn(("pqu-5", "exact_duplicate_in_source_base"), reasons)

    def test_parks_and_gym_are_kept_separately(self):
        parks = {i["place_id"] for i in self.review if i["reason"] == "not_found_in_current_ibram_geometry"}
        self.assertEqual(parks, {"ibram-8", "ibram-46"})
        gym = [i for i in self.review if i.get("place_id") == "sel-ginasio-samambaia"]
        self.assertEqual(len(gym), 1)
        self.assertEqual(gym[0]["category"], "non_park_venue")
        metrics = load("metricas.json")
        self.assertEqual(metrics["pending_parks_before"], 14)
        self.assertEqual(metrics["parks_resolved_official_geometry"] + metrics["parks_still_review"], 14)
        self.assertEqual(metrics["pending_non_park_venues"], 1)


if __name__ == "__main__":
    unittest.main()
