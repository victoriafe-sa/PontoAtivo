from __future__ import annotations

import json
import sys
from pathlib import Path

# Permite importar o pacote do projeto quando o script é executado.
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from pontoativo_rag.carregamento import (
    load_catalog,
    load_document,
    write_documents_jsonl,
)
from pontoativo_rag.processamento import (
    create_parent_chunks,
    create_embedding_segments,
    write_chunks_jsonl,
)


def main() -> None:
    catalog_path = ROOT / "dados" / "rag" / "catalogo.csv"

    output_dir = (
        ROOT
        / "docs"
        / "entregas"
        / "semana-06"
        / "multimodalidade-pdf-texto"
        / "resultados"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== DEMONSTRAÇÃO PDF + MARKDOWN ===")

    # Carrega os registros oficiais do catálogo.
    catalog = load_catalog(catalog_path)

    selected_ids = {"DOC-003", "DOC-025"}
    sources = [source for source in catalog if source.source_id in selected_ids]

    if len(sources) != 2:
        raise RuntimeError("Não foi possível localizar DOC-003 e DOC-025.")

    documents = []
    all_chunks = []
    all_segments = []
    report = []

    for source in sources:
        if not source.local_path:
            raise RuntimeError(
                f"A fonte {source.source_id} não possui caminho local."
            )

        document_path = Path(source.local_path)
        if not document_path.is_absolute():
            document_path = ROOT / document_path

        print(f"\nProcessando: {source.source_id}")
        print(f"Arquivo: {document_path.name}")

        # Carregamento e extração do conteúdo.
        document = load_document(document_path, source)
        documents.append(document)

        # Divisão em blocos e segmentos.
        chunks = create_parent_chunks(document)
        segments = [
            segment
            for chunk in chunks
            for segment in create_embedding_segments(chunk)
        ]

        all_chunks.extend(chunks)
        all_segments.extend(segments)

        item = {
            "source_id": source.source_id,
            "title": source.title,
            "format": document_path.suffix.lower(),
            "characters": len(document.text),
            "pages_with_text": len(document.pages),
            "pages_without_text": list(document.missing_pages),
            "pages_with_images": list(document.graphical_pages),
            "chunks": len(chunks),
            "segments": len(segments),
            "verification_status": source.verification_status,
            "sample": document.text[:300],
        }
        report.append(item)

        print(f"Caracteres extraídos: {len(document.text)}")
        print(f"Páginas com texto: {len(document.pages)}")
        print(f"Chunks criados: {len(chunks)}")
        print(f"Segmentos criados: {len(segments)}")

    # Salva os resultados somente na pasta isolada da demonstração.
    write_documents_jsonl(
        documents,
        output_dir / "documentos_normalizados.jsonl",
    )

    write_chunks_jsonl(
        all_chunks,
        output_dir / "chunks.jsonl",
    )

    with (output_dir / "segmentos.jsonl").open(
        "w", encoding="utf-8"
    ) as file:
        for segment in all_segments:
            data = {
                **segment.metadata(),
                "text": segment.text,
                "parent_text": segment.parent_text,
            }
            file.write(json.dumps(data, ensure_ascii=False) + "\n")

    summary = {
        "demonstracao": "Processamento de PDF e Markdown",
        "fontes_processadas": len(documents),
        "total_chunks": len(all_chunks),
        "total_segments": len(all_segments),
        "fontes": report,
        "observacao": (
            "O processamento extrai texto de PDF e Markdown. "
            "A identificação de páginas com imagens não significa "
            "interpretação visual ou execução de OCR."
        ),
    }

    with (output_dir / "relatorio.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print("\n=== DEMONSTRAÇÃO CONCLUÍDA ===")
    print(f"Fontes processadas: {len(documents)}")
    print(f"Total de chunks: {len(all_chunks)}")
    print(f"Total de segmentos: {len(all_segments)}")
    print(f"Resultados salvos em: {output_dir}")


if __name__ == "__main__":
    main()