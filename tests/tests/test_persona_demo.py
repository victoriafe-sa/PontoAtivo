from datetime import datetime

from pontoativo_rag.persona_demo import BRASILIA, LOCAL_ID, dados_da_corrida, proximo_horario


def test_corrida_e_hoje_as_18h_se_ainda_nao_passou():
    assert proximo_horario(datetime(2026, 11, 13, 16, 0, tzinfo=BRASILIA)) == datetime(2026, 11, 13, 18, 0, tzinfo=BRASILIA)


def test_depois_das_18h_a_corrida_vai_para_amanha():
    assert proximo_horario(datetime(2026, 11, 13, 18, 0, tzinfo=BRASILIA)) == datetime(2026, 11, 14, 18, 0, tzinfo=BRASILIA)


def test_corrida_em_grupo_no_pec_do_gama_com_id_estavel_por_dia():
    dados = dados_da_corrida(datetime(2026, 11, 13, 18, 0, tzinfo=BRASILIA))
    assert dados["local_id"] == LOCAL_ID and dados["formato"] == "grupo" and dados["esporte"] == "Corrida"
    assert dados["inicio"] == "2026-11-13T18:00:00-03:00"
    assert dados["request_id"] == "persona-jeferson-20261113"
