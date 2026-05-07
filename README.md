# patient-plan-explainer

> DICOM RT → patient-friendly treatment explanations.
> PDF and audio, in Brazilian Portuguese. Built for LATAM radiotherapy clinics.

**Status:** 🚧 Early development. v0.1 (PDF) coming soon.

## The clinical problem this solves

A radiotherapy treatment plan is born as a DICOM RT bundle: structured data
about prescriptions, beams, dose distributions, and target volumes. It is
written for treatment planning systems and clinical staff — not for the
person who is about to receive the treatment.

Patients arrive at their first consultation overwhelmed, often with limited
clinical literacy, and leave with a vague sense of "I'm going to get
radiation." In LATAM specifically the gap between what the clinical team understands
and what the patient understands is wide enough to affect adherence, 
anxiety, and outcomes.

This tool reads a DICOM RT plan and generates a one-page explanation in
plain Brazilian Portuguese — written for patients, designed to be reviewed
and signed by the responsible medical physicist before delivery.

## What it will do

- **Input:** DICOM RT plan (+ structure set, optionally dose).
- **Output v0.1 (PDF):** one-page A4 PDF with empathetic narrative,
  prescription summary, and a signature line for clinical review.
- **Output v0.2 (Audio):** 60-90s narration in Brazilian Portuguese,
  shareable via WhatsApp.
- **Output v0.3 (Spanish):** same flow in Spanish for broader LATAM reach.

## How it will work
