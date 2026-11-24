"""Gera entrada sintética controlada; não representa evento real."""
from pathlib import Path
import unicodedata
from PIL import Image, ImageDraw, ImageFont


def main():
    destino = Path(__file__).resolve().parents[1] / "docs/entregas/semana-06/multimodalidade-imagem-texto/cartaz-teste.png"
    imagem = Image.new("RGB", (1100, 800), "white")
    desenho = ImageDraw.Draw(imagem)
    fonte = ImageFont.load_default(size=36)
    linhas = ["CARTAZ FICTÍCIO — TESTE ACADÊMICO", "PontoAtivo: encontro esportivo",
              "Futsal: sábado, 9h", "Vôlei: sábado, 15h",
              "Local: Quadra Exemplo, Brasília", "Data: 12/12/2026",
              "Inscrição: na recepção", "Evento inventado para testar leitura de imagem."]
    for n, linha in enumerate(linhas):
        linha = unicodedata.normalize("NFKD", linha).encode("ascii", "ignore").decode()
        desenho.text((45, 45 + n * 85), linha, font=fonte, fill="black")
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(destino)
    print(destino)


if __name__ == "__main__":
    main()
