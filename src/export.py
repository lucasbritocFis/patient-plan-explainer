import io
import os
import wave
import struct
import asyncio
from datetime import datetime

import edge_tts
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from dotenv import load_dotenv

load_dotenv()

DISCLAIMER = (
    "Este documento e meramente informativo e nao substitui a orientacao "
    "do medico ou fisico medico responsavel pelo seu tratamento. "
    "Em caso de duvida, converse com sua equipe de saude."
)


# ==========================================
# 1. CLASSE DO PDF PROFISSIONAL
# ==========================================
class PDFProfissional(FPDF):
    def header(self):
        # Barra principal
        self.set_fill_color(15, 32, 65)
        self.rect(0, 0, 210, 28, 'F')

        # Linha de destaque
        self.set_fill_color(41, 128, 185)
        self.rect(0, 28, 210, 1.2, 'F')

        if os.path.exists("assets/logo.png"):
            self.image("assets/logo.png", 12, 4, 20)

        self.set_font("helvetica", "B", 15)
        self.set_text_color(255, 255, 255)
        self.set_y(5)
        self.cell(0, 9, "Guia do Seu Tratamento de Radioterapia", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("helvetica", "", 8)
        self.set_text_color(170, 195, 220)
        self.cell(0, 5, "Documento personalizado para o paciente", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(14)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(200, 210, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font("helvetica", "", 7)
        self.set_text_color(150, 150, 150)
        self.cell(95, 4, "Documento informativo - consulte sua equipe para duvidas clinicas",
                  align="L")
        self.cell(95, 4, f"Pagina {self.page_no()}/{{nb}}", align="R")


def _adicionar_secao(pdf, titulo):
    """Adiciona um título de seção com linha de destaque."""
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(15, 32, 65)
    pdf.cell(0, 10, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Sublinhado de destaque
    y = pdf.get_y()
    pdf.set_fill_color(41, 128, 185)
    pdf.rect(10, y, 35, 0.7, 'F')
    pdf.ln(4)


def _adicionar_quick_facts(pdf, dados):
    """Adiciona quadro de resumo técnico ao PDF."""
    _adicionar_secao(pdf, "Resumo do Tratamento")

    items = [
        ("Tecnica", dados.get("tecnica_provavel", "---")),
        ("Sessoes", str(dados.get("numero_fracoes", "---"))),
        ("Dose total", f"{dados.get('dose_total_gy', '---')} Gy"),
        ("Dose por sessao", f"{dados.get('dose_por_fracao_gy', '---')} Gy"),
        ("Equipamento", dados.get("maquina", "---")),
        ("Campos", str(dados.get("numero_campos", "---"))),
    ]

    for i, (label, valor) in enumerate(items):
        if i % 2 == 0:
            pdf.set_fill_color(242, 246, 252)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(50, 7, f"  {label}", border=0, fill=True)
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, valor, border=0, fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Borda inferior da tabela
    pdf.set_draw_color(200, 210, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)


def _adicionar_disclaimer(pdf):
    """Adiciona disclaimer regulatório e campo de assinatura."""
    pdf.ln(8)

    # Caixa do disclaimer
    y_start = pdf.get_y()
    pdf.set_fill_color(250, 245, 235)
    pdf.set_draw_color(220, 180, 120)
    pdf.rect(10, y_start, 190, 20, 'DF')

    pdf.set_xy(14, y_start + 3)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(160, 120, 60)
    pdf.cell(0, 4, "AVISO IMPORTANTE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(14)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(100, 80, 40)
    pdf.multi_cell(182, 4, DISCLAIMER)

    pdf.set_y(y_start + 24)

    # Campo de assinatura
    pdf.ln(6)
    pdf.set_draw_color(200, 200, 200)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "Revisado e aprovado por:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(2)
    y_line = pdf.get_y() + 6
    pdf.line(10, y_line, 110, y_line)
    pdf.line(120, y_line, 200, y_line)

    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.set_y(y_line + 2)
    pdf.cell(100, 4, "Nome e assinatura do profissional")
    pdf.cell(80, 4, "Data", align="L")


def gerar_pdf(texto_paciente, dados_extraidos=None):
    """Cria um arquivo PDF com layout profissional."""
    pdf = PDFProfissional()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    # Data de geração
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f"Gerado em: {datetime.now().strftime('%d/%m/%Y as %H:%M')}",
             align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # Quick-facts
    if dados_extraidos:
        _adicionar_quick_facts(pdf, dados_extraidos)

    # Narrativa
    _adicionar_secao(pdf, "Explicacao do Tratamento")

    pdf.set_font("helvetica", size=11)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 7, texto_paciente)

    # Disclaimer + assinatura
    _adicionar_disclaimer(pdf)

    return bytes(pdf.output())


# ==========================================
# 2. AUDIO COM VOZ HUMANA (GEMINI TTS)
# ==========================================
def _gerar_audio_gemini(texto):
    """Gera áudio com Gemini TTS — voz natural e humanizada."""
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não encontrada")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"Leia o texto abaixo em voz alta, de forma calma e acolhedora, "
                 f"como um profissional de saude conversando com o paciente:\n\n{texto}",
        config=types.GenerateContentConfig(
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore"
                    )
                )
            ),
        ),
    )

    audio_data = response.candidates[0].content.parts[0].inline_data.data

    # Converte PCM raw para WAV (24kHz, 16-bit, mono)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_data)
    buf.seek(0)
    return buf


async def _gerar_audio_edge_tts(texto):
    """Fallback: gera áudio com edge-tts."""
    communicate = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural", rate="+5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


def gerar_audio(texto_paciente):
    """
    Gera áudio humanizado. Tenta Gemini TTS primeiro, fallback para edge-tts.
    Retorna tupla (BytesIO, mime_type).
    """
    # Tenta Gemini TTS (voz natural)
    try:
        audio_buffer = _gerar_audio_gemini(texto_paciente)
        return audio_buffer, "audio/wav"
    except Exception:
        pass

    # Fallback: edge-tts
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    audio_bytes = loop.run_until_complete(_gerar_audio_edge_tts(texto_paciente))
    return io.BytesIO(audio_bytes), "audio/mp3"
