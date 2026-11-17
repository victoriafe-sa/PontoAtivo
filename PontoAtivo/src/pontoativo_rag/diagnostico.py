"""Diagnóstico executável do ambiente local do PontoAtivo."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen

from .configuracao import Settings


REQUIRED_DEPENDENCIES = (
    "pypdf",
    "bs4",
    "sentence_transformers",
    "chromadb",
    "httpx",
    "dotenv",
    "pytest",
)


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    checks: tuple[CheckResult, ...]

    @property
    def ready(self) -> bool:
        return all(check.ok for check in self.checks if check.required)

    @property
    def exit_code(self) -> int:
        return 0 if self.ready else 1

    def to_text(self) -> str:
        heading = "AMBIENTE PRONTO" if self.ready else "AMBIENTE COM PENDÊNCIAS"
        lines = [f"PONTOATIVO RAG — {heading}"]
        for check in self.checks:
            marker = "OK" if check.ok else "PENDENTE"
            optional = " (opcional)" if not check.required else ""
            lines.append(f"[{marker}] {check.name}{optional}: {check.detail}")
        return "\n".join(lines)


def _check_ollama(settings: Settings) -> CheckResult:
    try:
        with urlopen(
            f"{settings.ollama_base_url}/api/tags",
            timeout=settings.ollama_timeout_seconds,
        ) as response:
            payload = json.load(response)
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return CheckResult(
            name="ollama",
            ok=False,
            detail=f"serviço indisponível ({exc})",
        )

    models = {
        model.get("name")
        for model in payload.get("models", [])
        if isinstance(model, dict)
    }
    wanted = list(dict.fromkeys([settings.ollama_model, settings.map_model]))
    missing = [name for name in wanted if name not in models]
    if missing:
        return CheckResult(
            name="ollama",
            ok=False,
            detail=(
                "serviço ativo, mas falta instalar "
                + ", ".join(repr(name) for name in missing)
            ),
        )
    return CheckResult(
        name="ollama",
        ok=True,
        detail="serviço ativo com " + " e ".join(wanted),
    )


def run_diagnostics(
    settings: Settings,
    *,
    dependency_names: Iterable[str] = REQUIRED_DEPENDENCIES,
    ollama_checker: Callable[[Settings], CheckResult] = _check_ollama,
) -> DiagnosticReport:
    """Inspeciona o ambiente sem importar modelos ou bancos vetoriais."""
    python_ok = sys.version_info >= (3, 11)
    checks: list[CheckResult] = [
        CheckResult(
            name="python",
            ok=python_ok,
            detail=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    ]

    directories = (
        settings.sources_dir,
        settings.data_dir,
        settings.vector_db_dir,
        settings.documentation_dir,
        settings.evidence_dir,
    )
    missing = [path.name for path in directories if not path.is_dir()]
    checks.append(
        CheckResult(
            name="diretorios",
            ok=not missing,
            detail="presentes" if not missing else "ausentes: " + ", ".join(missing),
        )
    )

    for dependency in dependency_names:
        installed = importlib.util.find_spec(dependency) is not None
        checks.append(
            CheckResult(
                name=f"dependencia:{dependency}",
                ok=installed,
                detail="instalada" if installed else "não instalada",
            )
        )

    checks.append(ollama_checker(settings))
    return DiagnosticReport(tuple(checks))


def main() -> int:
    settings = Settings.from_env()
    settings.ensure_directories()
    report = run_diagnostics(settings)
    print(report.to_text())
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

