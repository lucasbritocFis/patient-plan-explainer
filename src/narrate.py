import os
import json
from pathlib import Path
from google import genai
from dotenv import load_dotenv

load_dotenv()

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _carregar_prompt(dados_extraidos):
    """Carrega o prompt de prompts/pt_br.md e injeta os dados."""
    prompt_path = PROMPT_DIR / "pt_br.md"
    template = prompt_path.read_text(encoding="utf-8")

    return template.format(
        dados_tecnicos=json.dumps(dados_extraidos, indent=2, ensure_ascii=False),
        numero_fracoes=dados_extraidos.get("numero_fracoes", "algumas"),
        numero_campos=dados_extraidos.get("numero_campos", "várias"),
    )


def gerar_explicacao_paciente(dados_extraidos):
    """
    Recebe os dados do DICOM e usa o LLM para gerar uma explicação empática.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Erro: Chave GEMINI_API_KEY não encontrada no arquivo .env."

    try:
        client = genai.Client(api_key=api_key)

        prompt = _carregar_prompt(dados_extraidos)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text

    except Exception as e:
        return f"⚠️ Erro ao comunicar com a Inteligência Artificial: {e}"
