# Deployment

## Streamlit Community Cloud

Current deployment: https://voc-h-intelligence.streamlit.app/

Deploy `app.py` from the `main` branch of `Parthhhhhh30/voc-product-intelligence`.

The app runs without AI credentials in deterministic demo mode. To enable live extraction and ticket drafting, add this secret in the Streamlit app settings:

```toml
GEMINI_API_KEY = "YOUR_KEY"
```

Do not commit the key to GitHub. `.streamlit/secrets.toml` and `.env` are ignored by Git.

## Post-deploy checks

1. Open **Operating contract** and run the explicit **live AI connection check**. A configured key alone is not treated as proof of a working model request.
2. Open **Research desk** and confirm 30 synthetic feedback items load.
3. Run **live AI extraction** on one feedback item after the secret is configured.
4. Approve the extraction and confirm the reviewed values appear in the theme board for the session.
5. Open **Evidence ledger** and confirm supporting conversations are visible.
6. Open **Problem memo**, draft a ticket, and confirm there is no recommended-feature field.
7. Confirm the footer states that the build is an independent portfolio prototype with no automated external actions.

## Verified deployment state

On 2 October 2026, the deployed app was manually checked with the configured Gemini secret. Both live AI workflows succeeded:

1. feedback extraction from **Research desk**
2. structured problem-ticket drafting from **Problem memo**

The latest automated workflow also passed all tests, compile checks, Streamlit session checks and the runtime health smoke test.
