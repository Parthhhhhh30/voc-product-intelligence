# AI Voice-of-Customer → Product Intelligence Engine

Independent portfolio prototype for a B2B healthtech product-operations workflow.

The engine turns customer evidence into reviewable product intelligence without allowing an LLM to jump directly from a complaint to a feature recommendation:

**customer feedback → AI candidate extraction → human review → deterministic theme aggregation → frequency + impact evidence → problem brief → AI ticket draft → human validation → solution discovery later**

## Why this project exists

The target Special Projects workflow requires customer insight, onboarding/support feedback, cross-functional product communication, operational process building and responsible use of AI. This project goes deeper than a generic sentiment dashboard by preserving the evidence chain from the original conversation through to a product problem brief.

## Demo dataset

- 30 synthetic B2B customer conversations
- channels: onboarding calls, support messages, customer check-ins
- no patient-level, clinical or real customer information
- six recurring operational/product themes
- fixed reviewed demo annotations make aggregation reproducible
- live Gemini analysis can re-analyse an individual conversation once a key is configured

## Workspace

- **Inbox** — source feedback, live AI extraction, editable human review and session approval
- **Theme board** — transparent recurring-theme aggregation and attention bands
- **Evidence** — supporting excerpts plus channel/stage distributions
- **Problem briefs** — evidence-led product/operations tickets with no feature-recommendation field
- **Method** — AI/deterministic/human boundaries and data safeguards

## Decision boundary

AI may extract, classify and draft. Deterministic code owns counts, shares, aggregation and attention-band rules. Humans own approval, impact judgement, customer follow-up, backlog priority and solution decisions.

The core product principle is:

**evidence → understand problem → validate → solution**

not:

**complaint → AI feature idea**

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional live AI:

```bash
export GEMINI_API_KEY="..."
```

## Quality checks

```bash
PYTHONPATH=. pytest -q
python -m py_compile app.py workspace.py analysis_engine.py synthetic.py taxonomy.py ai_layer.py scripts/verify_streamlit_session.py
PYTHONPATH=. python scripts/verify_streamlit_session.py
```

## Portfolio boundaries

This is an independent prototype. It does not use Healthtech-1 internal data, patient data, real customer calls or a real product backlog. The synthetic examples are designed to demonstrate the operating method rather than claim actual product findings.
