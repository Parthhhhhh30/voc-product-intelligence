# Live QA record

Date: 2 October 2026

Deployment: https://voc-h-intelligence.streamlit.app/

## Manual checks completed

- Research desk loads the synthetic conversation set.
- Live Gemini **Analyse this note** succeeds.
- The returned extraction remains editable before approval.
- Theme aggregation remains deterministic and review-driven.
- Evidence ledger preserves supporting excerpts.
- Live Gemini **Draft structured product ticket** succeeds.
- The ticket contains problem, evidence, operational impact, uncertainty and a validation next step.
- There is no recommended-feature field.
- No external CRM, ticketing or backlog action is performed automatically.

## Automated checks

Latest GitHub Actions head passes:

- pytest
- Python compilation
- full Streamlit session test
- Streamlit runtime health smoke

## Claim boundary

This QA confirms that the deployed portfolio prototype works as designed. It does not validate real Healthtech-1 customer findings, production security, clinical safety, NHS deployment readiness or product-market fit.
