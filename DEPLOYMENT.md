# Deployment

## Streamlit Community Cloud

Deploy `app.py` from the `main` branch of `Parthhhhhh30/voc-product-intelligence`.

The app runs without AI credentials in deterministic demo mode. To enable live extraction and ticket drafting, add this secret in the Streamlit app settings:

```toml
GEMINI_API_KEY = "YOUR_KEY"
```

Do not commit the key to GitHub. `.streamlit/secrets.toml` and `.env` are ignored by Git.

## Post-deploy checks

1. Open **Inbox** and confirm 30 synthetic feedback items load.
2. Run **live AI extraction** on one feedback item after the secret is configured.
3. Approve the extraction and confirm the reviewed values appear in the theme board for the session.
4. Open **Evidence** and confirm supporting conversations are visible.
5. Open **Problem briefs**, draft a ticket, and confirm there is no recommended-feature field.
6. Confirm the footer states that the build is an independent portfolio prototype with no automated external actions.
