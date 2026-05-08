# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Patient Plan Explainer converts DICOM RT radiotherapy treatment plans into patient-friendly explanations in Brazilian Portuguese. It reads RTPLAN and RTSTRUCT files, generates an empathetic narrative via Gemini LLM, and exports PDF and audio outputs. Designed for LATAM radiotherapy clinics.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Run tests
python -m pytest tests/ -v
```

Requires a `GEMINI_API_KEY` in `.env` file (see `.env.example`).

## Architecture

**Entry point:** `app.py` — Streamlit UI. Accepts two DICOM file uploads (RTPLAN + RTSTRUCT), orchestrates the three-phase pipeline, and renders results. Catches `ErroValidacaoDICOM` for user-friendly error messages.

**Pipeline (3 phases):**

1. **Extract** (`src/extract.py`) — Reads DICOM files with pydicom. `validar_arquivo_dicom()` validates files before processing. Identifies treatment technique (VMAT/IMRT/3D/SBRT) by inspecting beam physics (BeamType, GantryRotationDirection), not plan labels. Extracts: dose total, dose per fraction, fractions, beam energy (including FFF detection), machine name, target volumes (PTV/CTV/GTV), and OARs. Infers treatment intent (curativo/paliativo) via label heuristics and dose thresholds. Detects SBRT/hypofractionation when dose_per_fraction >= 6 Gy and fractions <= 8.

2. **Narrate** (`src/narrate.py`) — Loads prompt template from `prompts/pt_br.md` and injects extracted data. Auto-discovers available Gemini models at runtime, preferring "flash" variants. The prompt enforces strict communication rules: plain language, no jargon, 3 short paragraphs, no bullet points.

3. **Export** (`src/export.py`) — Two outputs:
   - **PDF**: Uses fpdf2 with branded header/footer, quick-facts summary table, narrative section, regulatory disclaimer, and signature line for clinical review. Looks for `assets/logo.png` for the header.
   - **Audio**: Uses `edge-tts` with Brazilian Portuguese neural voice `pt-BR-FranciscaNeural`. Handles async-to-sync bridging for Streamlit.

## Key Design Decisions

- Prompt is externalized in `prompts/pt_br.md` for easy iteration without code changes
- PDF always includes a fixed (non-LLM-generated) regulatory disclaimer and signature field
- `gerar_pdf()` accepts optional `dados_extraidos` dict to render quick-facts sidebar
- All UI text, prompts, and output are in Brazilian Portuguese (pt-BR)
