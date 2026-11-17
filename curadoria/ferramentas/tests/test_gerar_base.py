import json, tempfile, unittest
from pathlib import Path
from ferramentas.gerar_base import generate

class GeneratorTest(unittest.TestCase):
    def test_generator_is_idempotent_and_preserves_attribute_evidence(self):
        root=Path(__file__).parents[2]
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"a.js"; b=Path(td)/"b.js"
            records=generate(root.parent/"site"/"data"/"locais.js",root/"data"/"curadoria",a)
            records2=generate(a,root/"data"/"curadoria",b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            park=next(x for x in records if x["id"]=="ibram-4")
            self.assertEqual(park["evidence"]["coordinates"]["level"],"oficial")
            self.assertEqual(park["evidence"]["accessibility"]["level"],"desconhecido")
            self.assertTrue(any(x.get("ownership")=="private" for x in records2))

if __name__ == "__main__": unittest.main()
