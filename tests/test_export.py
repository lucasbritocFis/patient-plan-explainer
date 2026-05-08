"""Testes para o módulo de exportação PDF."""
from src.export import gerar_pdf


def test_gerar_pdf_retorna_bytes():
    """PDF deve ser gerado sem erro e retornar bytes válidos."""
    texto = "Este e um texto de teste para o paciente."
    dados = {
        "tecnica_provavel": "VMAT",
        "numero_fracoes": 25,
        "dose_total_gy": 50.0,
        "dose_por_fracao_gy": 2.0,
        "maquina": "TrueBeam",
        "numero_campos": 2,
    }
    resultado = gerar_pdf(texto, dados)

    assert isinstance(resultado, bytes)
    assert len(resultado) > 100
    assert resultado[:5] == b"%PDF-"


def test_gerar_pdf_sem_dados_extraidos():
    """PDF deve funcionar mesmo sem dados técnicos (backward compat)."""
    resultado = gerar_pdf("Texto simples de teste.")

    assert isinstance(resultado, bytes)
    assert resultado[:5] == b"%PDF-"
