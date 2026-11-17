from pathlib import Path

from pontoativo_rag.configuracao import Settings
from pontoativo_rag.diagnostico import CheckResult, run_diagnostics


def test_diagnostico_informa_dependencias_e_diretorios(tmp_path: Path) -> None:
    settings = Settings.from_env(root=tmp_path)

    report = run_diagnostics(
        settings,
        dependency_names=("pytest", "pacote_que_nao_existe_pontoativo"),
        ollama_checker=lambda _: CheckResult(
            name="ollama", ok=False, detail="serviço indisponível"
        ),
    )

    checks = {check.name: check for check in report.checks}
    assert checks["python"].ok is True
    assert checks["diretorios"].ok is False
    assert checks["dependencia:pytest"].ok is True
    assert checks["dependencia:pacote_que_nao_existe_pontoativo"].ok is False
    assert checks["ollama"].ok is False
    assert report.ready is False


def test_diagnostico_fica_pronto_com_diretorios_e_checks_verdes(
    tmp_path: Path,
) -> None:
    settings = Settings.from_env(root=tmp_path)
    settings.ensure_directories()

    report = run_diagnostics(
        settings,
        dependency_names=("pytest",),
        ollama_checker=lambda _: CheckResult(
            name="ollama", ok=True, detail="modelo disponível"
        ),
    )

    assert report.ready is True
    assert report.exit_code == 0
    assert "AMBIENTE PRONTO" in report.to_text()


def test_ollama_indisponivel_nao_interrompe_o_diagnostico(tmp_path: Path) -> None:
    settings = Settings.from_env(root=tmp_path)
    settings.ensure_directories()

    report = run_diagnostics(
        settings,
        dependency_names=("pytest",),
        ollama_checker=lambda _: CheckResult(
            name="ollama", ok=False, detail="conexão recusada"
        ),
    )

    assert report.ready is False
    assert report.exit_code == 1
    assert "conexão recusada" in report.to_text()
