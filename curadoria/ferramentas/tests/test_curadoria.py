import json
import unittest
from datetime import date
from pathlib import Path

from ferramentas.curadoria import Evidence, find_duplicate_candidates, merge_place, normalize_place, validate_place


FIXTURE = Path(__file__).parent / "fixtures" / "locais_minimos.json"


class CuradoriaTest(unittest.TestCase):
    def setUp(self):
        self.sources = {"ide_df": {"checked_at": "2026-11-10", "url": "https://example.gov.br"}}
        self.place = json.loads(FIXTURE.read_text())[0]

    def test_evidence_levels_are_restricted(self):
        self.assertEqual(Evidence(True, "oficial", "ide_df", "2025-01-01", "2026-11-10").level, "oficial")
        with self.assertRaises(ValueError):
            Evidence(True, "confirmado")

    def test_published_evidence_requires_source_and_dates(self):
        broken = normalize_place(self.place)
        broken["evidence"]["location"].pop("source_id")
        codes = {issue.code for issue in validate_place(broken, self.sources, date(2026, 11, 10))}
        self.assertIn("missing_source", codes)

    def test_field_evidence_requires_date_and_attachment(self):
        broken = normalize_place(self.place)
        broken["evidence"]["step_free_route"] = {"value": True, "level": "campo", "checked_at": "2026-11-10"}
        codes = {issue.code for issue in validate_place(broken, self.sources, date(2026, 11, 10))}
        self.assertIn("field_evidence_incomplete", codes)

    def test_coordinates_outside_df_are_rejected(self):
        broken = normalize_place(self.place)
        broken["latitude"], broken["longitude"] = -23.5, -46.6
        self.assertIn("outside_df", {i.code for i in validate_place(broken, self.sources, date(2026, 11, 10))})

    def test_old_source_is_kept_with_warning(self):
        old = normalize_place(self.place)
        old["evidence"]["location"]["source_date"] = "2023-01-01"
        issues = validate_place(old, self.sources, date(2026, 11, 10))
        self.assertTrue(any(i.code == "stale_source" and i.severity == "warning" for i in issues))

    def test_nearby_different_name_is_possible_duplicate(self):
        candidate = {**self.place, "id": "pec-b", "name": "Academia comunitária QNM 10", "latitude": -15.8144}
        matches = find_duplicate_candidates(candidate, [self.place])
        self.assertEqual(matches[0].status, "possible_duplicate")

    def test_merge_preserves_per_attribute_evidence(self):
        candidate = normalize_place(self.place)
        candidate["evidence"]["accessible_toilet"] = {"value": True, "level": "organizacao", "source_id": "ide_df", "source_date": "2026-01-01", "checked_at": "2026-11-10"}
        merged = merge_place(self.place, candidate).record
        self.assertEqual(merged["evidence"]["location"]["level"], "oficial")
        self.assertEqual(merged["evidence"]["accessible_toilet"]["level"], "organizacao")


if __name__ == "__main__":
    unittest.main()
