"""Importação dos parquinhos (parques infantis) da IDE-DF."""
import json
import tempfile
import unittest
from pathlib import Path

from ferramentas.curadoria import validate_place
from ferramentas.gerar_base import generate, legacy_evidence
from ferramentas.importar_parquinhos import build, eh_parquinho, to_record

GAMA = [("Gama", [[[-48.10, -16.05], [-48.10, -15.99], [-48.02, -15.99], [-48.02, -16.05], [-48.10, -16.05]]])]
SUDOESTE = [("Sudoeste/octogonal", [[[-47.94, -15.80], [-47.94, -15.78], [-47.91, -15.78], [-47.91, -15.80], [-47.94, -15.80]]])]


def feature(oid, tipo="PARQUE INFANTIL", x=-48.06, y=-16.02, **attrs):
    base = {"objectid_12": oid, "elm_tp_mobiliario": tipo, "elm_endereco": "QR827",
            "elm_data_atual": 1446336000000, "elm_ilum_pub": "SIM", "elm_est_conser": "BOM"}
    return {"attributes": {**base, **attrs}, "geometry": {"x": x, "y": y}}


class ParquinhosTest(unittest.TestCase):
    def test_as_quatro_grafias_do_cadastro_sao_parquinho(self):
        for tipo in ("PARQUE INFANTIL", "PARQUE INFANTIL ", "PARQUE_INFANTIL", "PARQUE_INFANTIL "):
            self.assertTrue(eh_parquinho(tipo), tipo)
        self.assertFalse(eh_parquinho("PEC"))

    def test_registro_tem_fonte_data_e_aviso_de_confirmar_no_local(self):
        rec = to_record(feature(7), GAMA, [])
        self.assertEqual((rec["id"], rec["t"], rec["ra"], rec["end"]), ("pin-7", "parquinho", "Gama", "QR 827"))
        self.assertEqual(rec["n"], "Parquinho – QR 827")
        self.assertEqual(rec["data"], "11/2015")
        self.assertTrue(rec["luz"] and rec["gratis"])
        self.assertEqual(rec["cons"], "Bom")
        self.assertIn("confirme no local", rec["obs"])
        self.assertIn("IDE-DF", rec["fonte"])
        rec["evidence"] = legacy_evidence(rec)
        rec["ownership"] = "public"
        fontes = {s["id"]: s for s in json.loads((Path(__file__).resolve().parents[2] / "data/curadoria/fontes.json").read_text(encoding="utf-8"))}
        place = {**rec, "name": rec["n"], "latitude": rec["lat"], "longitude": rec["lon"]}
        self.assertEqual([i for i in validate_place(place, fontes) if i.severity == "error"], [])

    def test_coordenada_nan_e_fora_das_ras_ficam_de_fora(self):
        self.assertIsNone(to_record(feature(1, x="NaN", y="NaN"), GAMA, []))
        self.assertIsNone(to_record(feature(2, x=-47.0, y=-15.0), GAMA, []))

    def test_registros_repetidos_no_mesmo_ponto_viram_um(self):
        dois = [feature(1), feature(2, x=-48.06005, y=-16.02005), feature(3, x=-48.07, y=-16.03)]
        self.assertEqual([r["id"] for r in build(dois, GAMA, [])], ["pin-1", "pin-3"])

    def test_nome_da_ra_sudoeste_fica_com_maiuscula(self):
        rec = to_record(feature(9, x=-47.925, y=-15.79), SUDOESTE, [])
        self.assertEqual(rec["ra"], "Sudoeste/Octogonal")

    def test_gerar_base_inclui_os_parquinhos(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            base = td / "base.js"
            base.write_text("window.PA_LOCAIS = [];\n", encoding="utf-8")
            cur = td / "curadoria"
            cur.mkdir()
            (cur / "parquinhos.json").write_text(json.dumps([to_record(feature(7), GAMA, [])]), encoding="utf-8")
            recs = generate(base, cur, td / "saida.js")
        self.assertEqual([(r["id"], r["t"], r["ownership"]) for r in recs], [("pin-7", "parquinho", "public")])
        self.assertEqual(recs[0]["evidence"]["address"]["level"], "oficial")


if __name__ == "__main__":
    unittest.main()
