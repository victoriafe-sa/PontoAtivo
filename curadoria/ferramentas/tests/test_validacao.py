"""Regras de validação acrescentadas após o diagnóstico (datas desconhecidas explícitas e coordenadas)."""
import unittest
from datetime import date

from ferramentas.curadoria import validate_place

SOURCES = {"ide_df": {"checked_at": "2026-11-10"}}
TODAY = date(2026, 11, 10)


def place(**evidence):
    return {"id": "x", "name": "X", "latitude": -15.8, "longitude": -47.9, "evidence": evidence}


def codes(record):
    return {(i.code, i.severity) for i in validate_place(record, SOURCES, TODAY)}


class SourceDateTest(unittest.TestCase):
    def test_missing_source_date_without_declaration_is_error(self):
        rec = place(address={"value": "Q 1", "level": "oficial", "source_id": "ide_df", "checked_at": "2026-11-05"})
        self.assertIn(("missing_date", "error"), codes(rec))

    def test_declared_unknown_source_date_is_review_not_error(self):
        rec = place(address={"value": "Q 1", "level": "oficial", "source_id": "ide_df", "checked_at": "2026-11-05", "source_date_unknown": True})
        result = codes(rec)
        self.assertIn(("source_date_unknown", "review"), result)
        self.assertNotIn(("missing_date", "error"), result)

    def test_checked_at_is_always_required(self):
        rec = place(address={"value": "Q 1", "level": "oficial", "source_id": "ide_df", "source_date_unknown": True})
        self.assertIn(("missing_date", "error"), codes(rec))

    def test_year_only_source_date_is_parsed_and_old_one_warns(self):
        rec = place(address={"value": "Q 1", "level": "oficial", "source_id": "ide_df", "source_date": "2020", "checked_at": "2026-11-10"})
        self.assertIn(("stale_source", "warning"), codes(rec))

    def test_old_source_keeps_its_date(self):
        ev = {"value": "Q 1", "level": "oficial", "source_id": "ide_df", "source_date": "10/2017", "checked_at": "2026-11-05"}
        validate_place(place(address=ev), SOURCES, TODAY)
        self.assertEqual(ev["source_date"], "10/2017")


class CoordinatesTest(unittest.TestCase):
    def test_coordinates_evidence_without_coordinates_is_error(self):
        rec = place(coordinates={"value": True, "level": "oficial", "source_id": "ide_df", "source_date": "2026-01-01", "checked_at": "2026-11-10"})
        rec["latitude"] = rec["longitude"] = None
        self.assertIn(("coordinates_missing", "error"), codes(rec))

    def test_unknown_coordinates_without_pin_are_valid(self):
        rec = place(coordinates={"value": None, "level": "desconhecido"})
        rec["latitude"] = rec["longitude"] = None
        self.assertFalse({c for c, s in codes(rec) if s == "error"})

    def test_pin_without_coordinate_evidence_is_error(self):
        rec = place(coordinates={"value": None, "level": "desconhecido"})
        self.assertIn(("coordinates_unsourced", "error"), codes(rec))


if __name__ == "__main__":
    unittest.main()
