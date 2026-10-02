# Architecture

## Flow

1. Feedback enters from a customer-facing channel.
2. Gemini returns a structured **candidate extraction** against a controlled taxonomy.
3. A human can edit and approve the extraction.
4. Deterministic code groups reviewed items into recurring themes and calculates frequency.
5. Operational impact remains visible separately from frequency.
6. Explicit rules assign an attention band; there is no opaque propensity or priority score.
7. A selected theme opens an evidence room showing the original supporting excerpts.
8. A problem brief is built from the reviewed evidence.
9. Gemini may format the brief into a reviewable ticket, but the schema contains no feature recommendation.
10. A human validates the problem before any solution work begins.

## Controlled taxonomy

The live extractor maps feedback to one of a small set of operational/product themes. An `Other / needs review` route exists so the model is not forced to create false certainty.

## Attention-band rules

- **High attention**: High impact with at least 3 conversations, or at least 20% of the sample.
- **Investigate**: at least 3 conversations, or High impact.
- **Monitor**: everything else.

These are prototype design rules, not company or NHS standards.

## Reliability

- AI failure cannot change theme counts because aggregation only uses the reviewed layer.
- Gemini calls use bounded retries for transient 429/5xx errors and a stable Flash fallback.
- The application still renders and aggregates without an API key.
- Fixed synthetic reviewed annotations keep the portfolio demo reproducible.
- Streamlit session tests exercise the rendered app in CI.

## Privacy boundary

The demo contains no patient names, NHS numbers, dates of birth, diagnoses, medication or clinical decision-making. A production version would require authorised source integrations, access controls, retention rules, audit logs, security review and appropriate governance before processing real customer material.
