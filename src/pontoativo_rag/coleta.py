"""Coleta reproduzível das fontes catalogadas (snapshot local + integridade).

Para cada linha do catálogo com URL em ``location`` e caminho em ``local_path``:

1. baixa a fonte se a cópia local ainda não existir;
2. confere se o conteúdo condiz com o tipo declarado (PDF ou HTML);
3. registra ``collected_at`` e o ``checksum_sha256`` no próprio catálogo.

Uso:

    python -m pontoativo_rag.coleta            # baixa apenas o que falta
    python -m pontoativo_rag.coleta --verificar  # só confere a integridade
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .configuracao import Settings


USER_AGENT = "PontoAtivo-RAG/0.1 (prototipo academico; coleta de fontes publicas)"


@dataclass(frozen=True, slots=True)
class CollectionResult:
    source_id: str
    status: str  # baixado | existente | integro | alterado | falha
    detail: str = ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def content_matches_type(content: bytes, document_type: str) -> bool:
    """Evita salvar páginas de erro como se fossem o documento esperado."""
    kind = document_type.lower()
    head = content[:2048].lstrip().lower()
    if kind == "pdf":
        return content.startswith(b"%PDF")
    if kind in {"html", "htm"}:
        return b"<html" in head or b"<!doctype html" in head
    return bool(content.strip())


def _read_catalog(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def _write_catalog(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _ssl_context():
    """Usa o repositório de certificados do sistema operacional.

    Alguns sites públicos enviam a cadeia de certificados incompleta. O
    Windows e o macOS completam a cadeia (como os navegadores); o pacote
    padrão do Python não. A verificação TLS permanece sempre ativa.
    """
    import ssl

    try:
        import truststore
    except ImportError:
        return True
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def _download(url: str, timeout: float) -> bytes:
    import httpx

    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
        verify=_ssl_context(),
    )
    response.raise_for_status()
    return response.content


def collect_sources(
    settings: Settings,
    catalog_path: Path,
    *,
    verify_only: bool = False,
    timeout: float = 60.0,
    downloader=_download,
    today: date | None = None,
) -> list[CollectionResult]:
    columns, rows = _read_catalog(catalog_path)
    for required in ("local_path", "collected_at", "checksum_sha256"):
        if required not in columns:
            columns.append(required)
    results: list[CollectionResult] = []
    collected_on = (today or date.today()).isoformat()

    for row in rows:
        source_id = row["source_id"]
        url = row.get("location", "")
        relative = row.get("local_path", "")
        if not relative:
            results.append(CollectionResult(source_id, "falha", "local_path vazio"))
            continue
        path = settings.root / relative

        if path.is_file():
            checksum = sha256_file(path)
            recorded = row.get("checksum_sha256", "")
            if recorded and recorded != checksum:
                results.append(
                    CollectionResult(source_id, "alterado", "checksum difere do catálogo")
                )
                continue
            row["checksum_sha256"] = checksum
            if not row.get("collected_at"):
                row["collected_at"] = collected_on
            status = "integro" if verify_only else "existente"
            results.append(CollectionResult(source_id, status))
            continue

        if verify_only or not url.startswith(("http://", "https://")):
            results.append(CollectionResult(source_id, "falha", "cópia local ausente"))
            continue

        try:
            content = downloader(url, timeout)
        except Exception as error:  # rede, HTTP 4xx/5xx, timeout
            results.append(CollectionResult(source_id, "falha", f"download: {error}"))
            continue
        if not content_matches_type(content, row.get("document_type", "")):
            results.append(
                CollectionResult(
                    source_id,
                    "falha",
                    f"conteúdo não corresponde ao tipo {row.get('document_type')!r}",
                )
            )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        row["checksum_sha256"] = sha256_file(path)
        row["collected_at"] = collected_on
        results.append(CollectionResult(source_id, "baixado", f"{len(content)} bytes"))

    _write_catalog(catalog_path, columns, rows)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coleta das fontes do PontoAtivo.")
    parser.add_argument("--catalogo", type=Path, default=None)
    parser.add_argument(
        "--verificar", action="store_true", help="não baixa; apenas confere integridade"
    )
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    settings.ensure_directories()
    catalog = args.catalogo or settings.catalog_path
    results = collect_sources(settings, catalog, verify_only=args.verificar)
    for result in results:
        print(f"[{result.status.upper():9}] {result.source_id} {result.detail}")
    failures = [r for r in results if r.status in {"falha", "alterado"}]
    print(f"\n{len(results) - len(failures)} de {len(results)} fontes disponíveis localmente.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
