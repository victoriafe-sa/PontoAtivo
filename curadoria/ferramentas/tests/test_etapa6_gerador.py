"""Testes da Etapa 6: gerador, categorias, evidência por atributo e segurança da publicação."""
import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ferramentas.curadoria import validate_place
from ferramentas.gerar_base import (
    CATEGORY_CLUBE,
    DEFAULT_BACKUP_NAME,
    generate,
    publish_with_safety,
    read_js,
)

ROOT = Path(__file__).parents[2]
ORIGINAL_JS = ROOT.parent / "site" / "data" / "locais.js"
CURATED_DIR = ROOT / "data" / "curadoria"
# 1748 na base de 05/11 (pqu-5 duplicado 3x = 1746 únicos), +2 paradesporto, +4 privados = 1752,
# mais os espaços comunitários da IDE-DF importados em 12/11 (campos, quadras e praças).
# Também os parquinhos (parques infantis) da IDE-DF importados em 19/11.
ESPACOS = json.loads((CURATED_DIR / "espacos_comunitarios.json").read_text(encoding="utf-8"))
PARQUINHOS = json.loads((CURATED_DIR / "parquinhos.json").read_text(encoding="utf-8"))
EXPECTED_TOTAL = 1752 + len(ESPACOS) + len(PARQUINHOS)
SOURCES = {s["id"]: s for s in json.loads((CURATED_DIR / "fontes.json").read_text())}
TODAY = date(2026, 11, 10)


class GeneratorSafetyTest(unittest.TestCase):
    def test_default_output_does_not_overwrite_input_silently(self):
        # A chamada segura exige confirmação ou caminho explícito e nunca grava sem backup
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "locais.js"
            base.write_bytes(ORIGINAL_JS.read_bytes())
            h_before = hashlib.sha256(base.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                # tentar publicar com base inválida propositalmente deve falhar e preservar
                publish_with_safety(base, CURATED_DIR, base, validate_fn=lambda recs: [("erro_forcado", "error")])
            self.assertEqual(hashlib.sha256(base.read_bytes()).hexdigest(), h_before)

    def test_publish_creates_backup_and_preserves_checksum(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "locais.js"
            base.write_bytes(ORIGINAL_JS.read_bytes())
            backup = Path(td) / DEFAULT_BACKUP_NAME
            records = publish_with_safety(base, CURATED_DIR, base, backup_path=backup)
            self.assertTrue(backup.exists())
            self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(), hashlib.sha256(ORIGINAL_JS.read_bytes()).hexdigest())
            self.assertEqual(len(records), EXPECTED_TOTAL)


class GeneratorOutputIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.out = Path(cls.td.name) / "out.js"
        cls.records = generate(ORIGINAL_JS, CURATED_DIR, cls.out)
        cls.by_id = {r["id"]: r for r in cls.records}

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_total_places_and_ids(self):
        self.assertEqual(len(ESPACOS), 1348)
        self.assertEqual(len(PARQUINHOS), 809)
        self.assertEqual(sum(1 for r in self.records if r["t"] == "parquinho"), 809)
        self.assertEqual(len(self.records), EXPECTED_TOTAL)
        self.assertEqual(len(self.by_id), EXPECTED_TOTAL)

    def test_every_published_record_has_zero_validation_errors(self):
        all_errors = []
        for r in self.records:
            rec = {**r, "name": r["n"], "latitude": r.get("lat"), "longitude": r.get("lon")}
            errors = [i for i in validate_place(rec, SOURCES, TODAY) if i.severity == "error"]
            if errors:
                all_errors.append((r["id"], errors))
        self.assertEqual(all_errors, [])

    def test_stale_source_warnings_are_preserved(self):
        # Alertas de fontes antigas (2015–2017) continuam como warning de revisão (mais de 1600)
        warnings = 0
        for r in self.records:
            rec = {**r, "name": r["n"], "latitude": r.get("lat"), "longitude": r.get("lon")}
            warnings += sum(1 for i in validate_place(rec, SOURCES, TODAY) if i.code == "stale_source")
        self.assertGreater(warnings, 1600)

    def test_private_venues_use_clube_category_not_estadio(self):
        privates = [r for r in self.records if r.get("ownership") == "private" and r["id"].startswith("priv-")]
        self.assertEqual(len(privates), 4)
        for p in privates:
            self.assertEqual(p["t"], CATEGORY_CLUBE)
            self.assertEqual(p["ownership"], "private")

    def test_seven_undocumented_venues_have_no_pin_and_unknown_coords(self):
        seven = ["para-cetefe", "para-diref", "para-escola-fatima", "priv-clube-naval", "priv-aabb", "priv-minas", "priv-aeronautica"]
        for pid in seven:
            r = self.by_id[pid]
            if pid == "para-cetefe":
                # CETEFE preserva o ponto aproximado de 05/11 (OpenStreetMap, nível de bairro), declarado como aproximado
                self.assertIsNotNone(r["lat"])
                self.assertTrue(r.get("aprox"))
                self.assertEqual(r["evidence"]["coordinates"]["level"], "colaborativo")
            else:
                self.assertIsNone(r["lat"], pid)
                self.assertIsNone(r["lon"], pid)
                self.assertEqual(r["evidence"]["coordinates"]["level"], "desconhecido", pid)

    def test_separate_accessibility_attributes_are_exposed(self):
        sample = self.by_id["ide-2"]
        acc_ev = sample["evidence"]["accessibility_attributes"]
        self.assertIn("step_free_route", acc_ev)
        self.assertIn("accessible_toilet", acc_ev)
        self.assertIn("tactile_paving", acc_ev)
        self.assertIn("accessible_parking", acc_ev)
        self.assertIn("adapted_equipment", acc_ev)
        # Nenhuma acessibilidade inferida vira "campo"
        for r in self.records:
            for k, ev in r["evidence"]["accessibility_attributes"].items():
                self.assertNotEqual(ev.get("level"), "campo", f"{r['id']}.{k}")

    def test_cops_and_cetefe_adaptado_legacy_is_not_flattened_to_unknown(self):
        cop = self.by_id["cop-brazlandia"]
        self.assertEqual(cop["evidence"]["accessibility_attributes"]["adapted_equipment"]["level"], "oficial")
        self.assertEqual(cop["evidence"]["accessibility_attributes"]["adapted_equipment"]["value"], "info")
        cetefe = self.by_id["para-cetefe"]
        self.assertEqual(cetefe["evidence"]["accessibility_attributes"]["adapted_equipment"]["level"], "organizacao")

    def test_idempotent_reapplication(self):
        with tempfile.TemporaryDirectory() as td:
            second = Path(td) / "second.js"
            generate(self.out, CURATED_DIR, second)
            self.assertEqual(self.out.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
