from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import requests

from taxonomy import CONFIDENCE_LEVELS, IMPACT_LEVELS, THEMES, WORKFLOW_STAGES

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODELS = tuple(
    x.strip()
    for x in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.7-flash").split(",")
    if x.strip()
)
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
RETRYABLE = {429, 500, 502, 503, 504}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "problem": {"type": "string"},
        "theme": {"type": "string", "enum": list(THEMES)},
        "workflow_stage": {"type": "string", "enum": list(WORKFLOW_STAGES)},
        "impact_level": {"type": "string", "enum": list(IMPACT_LEVELS)},
        "impact_reason": {"type": "string"},
        "evidence": {"type": "string"},
        "confidence": {"type": "string", "enum": list(CONFIDENCE_LEVELS)},
        "needs_human_review": {"type": "boolean"},
    },
    "required": [
        "problem",
        "theme",
        "workflow_stage",
        "impact_level",
        "impact_reason",
        "evidence",
        "confidence",
        "needs_human_review",
    ],
    "additionalProperties": False,
}

TICKET_SCHEMA = {
    "type": "object",
    "properties": {
        "problem": {"type": "string"},
        "evidence": {"type": "string"},
        "operational_impact": {"type": "string"},
        "what_we_do_not_know_yet": {"type": "string"},
        "suggested_next_step": {"type": "string"},
    },
    "required": [
        "problem",
        "evidence",
        "operational_impact",
        "what_we_do_not_know_yet",
        "suggested_next_step",
    ],
    "additionalProperties": False,
}


def _api_key() -> str | None:
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st

        secret = st.secrets.get("GEMINI_API_KEY")
        return str(secret) if secret else None
    except Exception:
        return None


def available() -> bool:
    return bool(_api_key())


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidate output")
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [p.get("text", "") for p in parts if p.get("text")]
    if not texts:
        raise RuntimeError("Gemini returned no text output")
    return "\n".join(texts).strip()


def _error_detail(response) -> str:
    try:
        body = response.text or ""
    except Exception:
        body = ""
    body = re.sub(r"\s+", " ", body).strip()
    return body[:500]


def _config_variants(schema: dict[str, Any] | None) -> list[tuple[str, dict[str, Any]]]:
    base = {"thinkingConfig": {"thinkingLevel": "low"}}
    if schema is None:
        return [("plain", base)]

    # Current generateContent structured-output shape first.
    modern = {
        **base,
        "responseFormat": {
            "text": {
                "mimeType": "application/json",
                "schema": schema,
            }
        },
    }

    # Compatibility path still documented by Google for generateContent.
    legacy = {
        **base,
        "responseMimeType": "application/json",
        "responseSchema": schema,
    }

    # Last-resort provider compatibility path. We still validate the returned JSON
    # locally, so a provider-side schema-format change cannot break the operator UI.
    prompt_only = dict(base)
    return [("responseFormat", modern), ("responseSchema", legacy), ("prompt-json", prompt_only)]


def _generate(prompt: str, schema: dict[str, Any] | None = None) -> str:
    key = _api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    failures: list[str] = []
    models = (MODEL,) + tuple(x for x in FALLBACK_MODELS if x != MODEL)

    for model in models:
        for mode, generation_config in _config_variants(schema):
            request_prompt = prompt
            if schema is not None and mode == "prompt-json":
                request_prompt += (
                    "\n\nReturn JSON only. It must match this contract exactly:\n"
                    + json.dumps(schema, ensure_ascii=False)
                )

            payload = {
                "contents": [{"parts": [{"text": request_prompt}]}],
                "generationConfig": generation_config,
            }
            url = f"{BASE_URL}/{model}:generateContent"

            for attempt in range(3):
                try:
                    response = requests.post(
                        url,
                        headers={
                            "x-goog-api-key": key,
                            "Content-Type": "application/json",
                        },
                        json=payload,
                        timeout=45,
                    )
                except requests.RequestException as exc:
                    failures.append(f"{model}/{mode} {type(exc).__name__}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    break

                status = getattr(response, "status_code", 200)

                if status in RETRYABLE:
                    failures.append(f"{model}/{mode} HTTP {status}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    break

                # A 400 on a structured-output envelope can be caused by API-shape
                # compatibility. Try the next documented/local-validation mode.
                if status == 400 and schema is not None and mode != "prompt-json":
                    failures.append(
                        f"{model}/{mode} HTTP 400 {_error_detail(response)}".strip()
                    )
                    break

                if status >= 400:
                    detail = _error_detail(response)
                    raise RuntimeError(
                        f"Gemini request failed: HTTP {status}"
                        + (f" — {detail}" if detail else "")
                    )

                return _extract_text(response.json())

            # Continue to the next configuration mode for this model.

    detail = "; ".join(failures[-8:]) if failures else "no response details"
    raise RuntimeError(
        "AI service unavailable after retries and compatibility fallbacks. " + detail
    )


def _parse_json(raw: str) -> dict:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("AI output was not a JSON object")
    return value


def _validate_extraction(data: dict) -> dict:
    required = set(EXTRACTION_SCHEMA["required"])
    missing = required.difference(data)
    if missing:
        raise ValueError("AI extraction missing fields: " + ", ".join(sorted(missing)))
    if data["theme"] not in THEMES:
        raise ValueError("AI output used an unknown theme")
    if data["impact_level"] not in IMPACT_LEVELS:
        raise ValueError("AI output used an unknown impact level")
    if data["workflow_stage"] not in WORKFLOW_STAGES:
        raise ValueError("AI output used an unknown workflow stage")
    if data["confidence"] not in CONFIDENCE_LEVELS:
        raise ValueError("AI output used an unknown confidence level")
    if not isinstance(data["needs_human_review"], bool):
        raise ValueError("AI output used an invalid review flag")
    return data


def _validate_ticket(data: dict) -> dict:
    required = set(TICKET_SCHEMA["required"])
    missing = required.difference(data)
    if missing:
        raise ValueError("AI ticket missing fields: " + ", ".join(sorted(missing)))

    prohibited = {"feature", "recommended_feature", "solution", "recommended_solution"}
    if prohibited.intersection(data):
        raise ValueError("AI ticket crossed the problem-before-solution boundary")

    for key in required:
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValueError(f"AI ticket field {key} must be non-empty text")
    return data


def analyze_feedback(text: str, channel: str, workflow_stage: str) -> dict:
    prompt = f"""You are a B2B healthtech Voice-of-Customer analyst.
Extract ONE primary operational/product problem from the feedback below.
Use the controlled taxonomy exactly. Do not infer patient-level facts, clinical risk, customer intent, or a product solution.
Keep evidence grounded in the supplied feedback. Mark needs_human_review=true when uncertain.
Channel: {channel}
Current workflow stage: {workflow_stage}
Feedback: {text}
"""
    return _validate_extraction(_parse_json(_generate(prompt, EXTRACTION_SCHEMA)))


def draft_product_ticket(problem_brief: dict, evidence_examples: list[str]) -> dict:
    if not available():
        return {
            "problem": problem_brief["problem"],
            "evidence": (
                f"{problem_brief['evidence_count']} conversations "
                f"({problem_brief['evidence_share']:.0%}) in the reviewed demo set."
            ),
            "operational_impact": problem_brief["impact_reason"],
            "what_we_do_not_know_yet": problem_brief["what_we_do_not_know_yet"],
            "suggested_next_step": problem_brief["suggested_next_step"],
        }

    prompt = f"""Draft a product/operations problem ticket from reviewed Voice-of-Customer evidence.
Do NOT propose a feature or solution. The sequence is evidence -> understand -> validate -> solution later.
Preserve uncertainty and use only the supplied aggregate and excerpts.
Aggregate: {problem_brief}
Evidence excerpts: {evidence_examples}
"""
    return _validate_ticket(_parse_json(_generate(prompt, TICKET_SCHEMA)))


def connection_check() -> tuple[bool, str]:
    """Perform one explicit live model call. Never runs automatically."""
    if not available():
        return False, "API key is not configured"
    try:
        reply = _generate("Reply with exactly: CONNECTED")
        return ("CONNECTED" in reply.upper()), reply[:120]
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
