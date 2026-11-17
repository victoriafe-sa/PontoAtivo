"""Testes unitários detalhados da validação de contribuições comunitárias (Etapa 7)."""
import unittest
from ferramentas.curadoria import validate_community_submission


class ComprehensiveContributionTest(unittest.TestCase):
    def test_basic_submission_is_pending_and_collaborative(self):
        item = {
            "place_id": "ide-1",
            "kind": "accessibility",
            "consent": True,
            "answers": {"accessible_toilet": "ok"},
            "submitted_at": "2026-11-10T12:00:00Z",
        }
        res = validate_community_submission(item)
        self.assertTrue(res["valid"])
        self.assertEqual(res["status"], "pending_review")
        self.assertEqual(res["level"], "colaborativo")
        # Nunca vira campo sem vistoria técnica e moderação
        self.assertNotEqual(res["level"], "campo")

    def test_missing_consent_is_invalid(self):
        item = {
            "place_id": "ide-1",
            "kind": "accessibility",
            "consent": False,
            "answers": {"accessible_toilet": "ok"},
            "submitted_at": "2026-11-10T12:00:00Z",
        }
        res = validate_community_submission(item)
        self.assertFalse(res["valid"])
        self.assertIn("consent_required", res["errors"])

    def test_submission_with_photo_stays_pending(self):
        item = {
            "place_id": "ide-1",
            "kind": "accessibility",
            "consent": True,
            "answers": {"accessible_toilet": "ok"},
            "attachment": "data:image/png;base64,iVBORw0KGgo...",
            "submitted_at": "2026-11-10T12:00:00Z",
        }
        res = validate_community_submission(item)
        self.assertTrue(res["valid"])
        self.assertEqual(res["status"], "pending_review")
        self.assertEqual(res["level"], "colaborativo")

    def test_unknown_answers_accepted_as_pending(self):
        item = {
            "place_id": "ide-1",
            "kind": "accessibility",
            "consent": True,
            "answers": {"step_free_route": "unknown", "accessible_toilet": "unknown"},
            "submitted_at": "2026-11-10T12:00:00Z",
        }
        res = validate_community_submission(item)
        self.assertTrue(res["valid"])
        self.assertEqual(res["status"], "pending_review")


if __name__ == "__main__":
    unittest.main()
