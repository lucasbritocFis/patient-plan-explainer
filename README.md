# patient-plan-explainer

![CI](https://github.com/lucasbritocFis/patient-plan-explainer/actions/workflows/ci.yml/badge.svg)

> DICOM RT → patient-friendly treatment explanations.
> PDF and audio, in Brazilian Portuguese. Built for LATAM radiotherapy clinics.

## The clinical problem this solves

A radiotherapy treatment plan is born as a DICOM RT bundle: structured data about prescriptions, beams, dose distributions, and target volumes. It is written for treatment planning systems and clinical staff — not for the person who is about to receive the treatment.

Patients arrive at their first consultation overwhelmed, often with limited clinical literacy, and leave with a vague sense of "I'm going to get radiation." In LATAM specifically, the gap between what the clinical team understands and what the patient understands is wide enough to affect adherence, anxiety, and outcomes.

This tool reads a DICOM RT plan and generates a clear explanation in plain Brazilian Portuguese — written for patients, designed to be reviewed and signed by the responsible medical physicist before delivery.

## What it does

- **Input:** DICOM RT Plan (.dcm) + RT Structure Set (.dcm)
- **Output:** Patient-friendly narrative (text + PDF + audio)
  - PDF with treatment summary, empathetic explanation, regulatory disclaimer, and signature line for clinical review
  - Audio narration in Brazilian Portuguese (neural TTS), shareable via WhatsApp

## How it works

```
DICOM RT Plan + RT Struct
        │
        ▼
┌─────────────────┐
│   Extract        │  pydicom: technique (VMAT/IMRT/3D/SBRT),
│   (src/extract)  │  dose, fractions, machine, OARs, targets
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Narrate        │  Gemini LLM with controlled prompt
│   (src/narrate)  │  → empathetic text in PT-BR
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Export         │  PDF (fpdf2) + Audio (edge-tts)
│   (src/export)   │  with disclaimer + signature line
└─────────────────┘
```

## Quick start

```bash
# Clone
git clone https://github.com/lucasbritocFis/patient-plan-explainer.git
cd patient-plan-explainer

# Setup
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your Gemini API key (free at aistudio.google.com)

# Run
streamlit run app.py
```

Open `http://localhost:8501`, upload your RTPLAN and RTSTRUCT files, and click "Gerar Explicação Completa".

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Privacy & limitations

**This tool is not a medical device** and does not replace clinical consultation. Output must be reviewed and signed by a qualified medical physicist or radiation oncologist before being delivered to a patient.

DICOM data uploaded through this tool is processed by external LLM APIs (Google Gemini). **Use only anonymized or test data** unless your institutional privacy and regulatory review allows otherwise.

## Roadmap

- [x] v0.1 — PDF output, Brazilian Portuguese
- [x] v0.2 — Audio output (neural TTS)
- [ ] v0.3 — Spanish localization
- [ ] v0.4 — Visual companion (DVH, isodose overlays)
- [ ] v0.5 — Voice cloning of the responsible physicist (with consent)

## License

MIT — see [LICENSE](./LICENSE).

## Author

Lucas Brito, PhD — Medical Physicist & Software Developer
[GitHub](https://github.com/lucasbritocFis) · Rio de Janeiro, Brazil
