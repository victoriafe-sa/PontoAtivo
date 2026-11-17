"""Importação dos espaços comunitários da IDE-DF (campos, quadras e praças)."""
import json
import unittest
from pathlib import Path

from ferramentas.curadoria import validate_place
from ferramentas.gerar_base import legacy_evidence
from ferramentas.importar_espacos_comunitarios import build, representative_point, to_record

# Quadrado de ~20 m x ~30 m (600 m²) no Gama e a "RA" que o contém.
QUADRA = [[[-48.0600, -16.0200], [-48.0600, -16.0197293], [-48.0598131, -16.0197293], [-48.0598131, -16.0200], [-48.0600, -16.0200]]]
GAMA = [("Gama", [[[-48.10, -16.05], [-48.10, -15.99], [-48.02, -15.99], [-48.02, -16.05], [-48.10, -16.05]]])]


def feature(objectid, tipo, rings=QUADRA, **attrs):
    return {"attributes": {"objectid": objectid, "ec_tipo": tipo, "ec_ano": 2016, **attrs}, "geometry": {"rings": rings}}


class EspacosComunitariosTest(unittest.TestCase):
    def test_ponto_e_area_do_poligono(self):
        lat, lon, area = representative_point(QUADRA)
        self.assertAlmostEqual(lat, -16.019865, places=5)
        self.assertAlmostEqual(lon, -48.059907, places=5)
        self.assertTrue(560 <= area <= 640, area)

    def test_quadra_vira_registro_publico_com_regiao_da_poligonal(self):
        rec = to_record(feature(10, 7), GAMA, [])
        self.assertEqual(rec["id"], "epc-10")
        self.assertEqual(rec["t"], "quadra")
        self.assertEqual(rec["ra"], "Gama")
        self.assertEqual(rec["n"], "Quadra poliesportiva – Gama")
        self.assertIsNone(rec["end"])
        self.assertTrue(rec["gratis"])
        self.assertIn("Sem endereço no cadastro", rec["obs"])

    def test_codigos_sem_significado_confirmado_ficam_de_fora(self):
        for tipo in (2, 9, 10, 11, 12, 14, 15):
            self.assertIsNone(to_record(feature(1, tipo), GAMA, []), tipo)

    def test_fora_de_qualquer_ra_fica_de_fora(self):
        self.assertIsNone(to_record(feature(1, 7), [], []))

    def test_duplicata_da_base_publicada_e_entre_novos_fica_de_fora(self):
        lat, lon, _ = representative_point(QUADRA)
        publicada = [{"id": "ide-1", "t": "quadra", "lat": lat + 0.0001, "lon": lon}]
        self.assertIsNone(to_record(feature(1, 7), GAMA, publicada))
        # um campo no mesmo ponto não é duplicata de uma quadra
        self.assertIsNotNone(to_record(feature(1, 5), GAMA, publicada))
        novos = build([feature(1, 7), feature(2, 7)], GAMA, [])
        self.assertEqual([r["id"] for r in novos], ["epc-1"])

    def test_rodar_de_novo_sobre_a_base_publicada_da_o_mesmo_resultado(self):
        import tempfile
        from ferramentas.importar_espacos_comunitarios import read_places

        primeira = build([feature(1, 7)], GAMA, [])
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "locais.js"
            base.write_text("window.PA_LOCAIS = " + json.dumps(primeira) + ";\n", encoding="utf-8")
            self.assertEqual(read_places(base), [])  # os próprios epc- não contam como duplicata
            self.assertEqual(build([feature(1, 7)], GAMA, read_places(base)), primeira)

    def test_nome_proprio_e_endereco(self):
        praca = to_record(feature(3, 1, ec_endereco="QC 04 PRAÇA"), GAMA, [])
        self.assertEqual(praca["n"], "Praça – QC 04")
        nomeada = to_record(feature(4, 1, ec_nome="PRAÇA DOS CRISTAIS"), GAMA, [])
        self.assertEqual(nomeada["n"], "Praça dos Cristais")

    def test_registro_passa_na_validacao_como_fonte_oficial(self):
        fontes_path = Path(__file__).resolve().parents[2] / "data" / "curadoria" / "fontes.json"
        fontes = {s["id"]: s for s in json.loads(fontes_path.read_text(encoding="utf-8"))}
        rec = to_record(feature(10, 7), GAMA, [])
        rec["evidence"] = legacy_evidence(rec)
        self.assertEqual(rec["evidence"]["coordinates"]["source_id"], "ide_df_espacos_comunitarios")
        self.assertEqual(rec["evidence"]["coordinates"]["level"], "oficial")
        errors = [i for i in validate_place({**rec, "name": rec["n"], "latitude": rec["lat"], "longitude": rec["lon"]}, fontes) if i.severity == "error"]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
