from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import requests
from taxonomy import CONFIDENCE_LEVELS, IMPACT_LEVELS, THEMES, WORKFLOW_STAGES

MODEL=os.getenv("GEMINI_MODEL","gemini-3.8-flash")
FALLBACK_MODELS=tuple(x.strip() for x in os.getenv("GEMINI_FALLBACK_MODELS","gemini-3.7-flash").split(",") if x.strip())
BASE_URL="https://generativelanguage.googleapis.com/v1beta/models"
RETRYABLE={429,500,502,503,504}

EXTRACTION_SCHEMA={
    "type":"object",
    "properties":{
        "problem":{"type":"string"},
        "theme":{"type":"string","enum":list(THEMES)},
        "workflow_stage":{"type":"string","enum":list(WORKFLOW_STAGES)},
        "impact_level":{"type":"string","enum":list(IMPACT_LEVELS)},
        "impact_reason":{"type":"string"},
        "evidence":{"type":"string"},
        "confidence":{"type":"string","enum":list(CONFIDENCE_LEVELS)},
        "needs_human_review":{"type":"boolean"},
    },
    "required":["problem","theme","workflow_stage","impact_level","impact_reason","evidence","confidence","needs_human_review"],
    "additionalProperties":False,
}

TICKET_SCHEMA={
    "type":"object",
    "properties":{
        "problem":{"type":"string"},
        "evidence":{"type":"string"},
        "operational_impact":{"type":"string"},
        "what_we_do_not_know_yet":{"type":"string"},
        "suggested_next_step":{"type":"string"},
    },
    "required":["problem","evidence","operational_impact","what_we_do_not_know_yet","suggested_next_step"],
    "additionalProperties":False,
}

def _api_key()->str|None:
    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY")
    try:
        import streamlit as st
        key=st.secrets.get("GEMINI_API_KEY")
        return str(key) if key else None
    except Exception:
        return None

def available()->bool:
    return bool(_api_key())

def _generate(prompt:str,schema:dict[str,Any]|None=None)->str:
    key=_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    config={"thinkingConfig":{"thinkingLevel":"low"}}
    if schema is not None:
        config["responseFormat"]={"text":{"mimeType":"application/json","schema":schema}}
    payload={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":config}
    failures=[]
    for model in (MODEL,)+tuple(x for x in FALLBACK_MODELS if x!=MODEL):
        url=f"{BASE_URL}/{model}:generateContent"
        for attempt in range(3):
            try:
                r=requests.post(url,headers={"x-goog-api-key":key,"Content-Type":"application/json"},json=payload,timeout=45)
                status=getattr(r,"status_code",200)
                if status in RETRYABLE:
                    failures.append(f"{model} HTTP {status}")
                    if attempt<2:
                        time.sleep(2**attempt)
                        continue
                    break
                r.raise_for_status()
                data=r.json()
                candidates=data.get("candidates") or []
                if not candidates:
                    raise RuntimeError("Gemini returned no candidate output")
                parts=candidates[0].get("content",{}).get("parts",[])
                texts=[p.get("text","") for p in parts if p.get("text")]
                if not texts:
                    raise RuntimeError("Gemini returned no text output")
                return "\n".join(texts).strip()
            except requests.RequestException as exc:
                status=getattr(getattr(exc,"response",None),"status_code",None)
                failures.append(f"{model} {type(exc).__name__}" + (f" HTTP {status}" if status else ""))
                if status in RETRYABLE and attempt<2:
                    time.sleep(2**attempt)
                    continue
                if status not in RETRYABLE:
                    raise
    raise RuntimeError("AI service unavailable after retries/fallback. "+"; ".join(failures[-6:]))

def _parse_json(raw:str)->dict:
    raw=re.sub(r"^\`\`\`(?:json)?\s*","",raw.strip(),flags=re.I)
    raw=re.sub(r"\s*\`\`\`$","",raw)
    return json.loads(raw)

def analyze_feedback(text:str,channel:str,workflow_stage:str)->dict:
    prompt=f"""You are a B2B healthtech Voice-of-Customer analyst.
Extract ONE primary operational/product problem from the feedback below.
Use the controlled taxonomy exactly. Do not infer patient-level facts, clinical risk, customer intent, or a product solution.
Keep evidence grounded in the supplied feedback. Mark needs_human_review=true when uncertain.
Channel: {channel}
Current workflow stage: {workflow_stage}
Feedback: {text}
"""
    data=_parse_json(_generate(prompt,EXTRACTION_SCHEMA))
    if data["theme"] not in THEMES or data["impact_level"] not in IMPACT_LEVELS or data["workflow_stage"] not in WORKFLOW_STAGES or data["confidence"] not in CONFIDENCE_LEVELS:
        raise ValueError("AI output violated the controlled taxonomy")
    return data

def draft_product_ticket(problem_brief:dict,evidence_examples:list[str])->dict:
    if not available():
        return {
            "problem":problem_brief["problem"],
            "evidence":f"{problem_brief['evidence_count']} conversations ({problem_brief['evidence_share']:.0%}) in the reviewed demo set.",
            "operational_impact":problem_brief["impact_reason"],
            "what_we_do_not_know_yet":problem_brief["what_we_do_not_know_yet"],
            "suggested_next_step":problem_brief["suggested_next_step"],
        }
    prompt=f"""Draft a product/operations problem ticket from reviewed Voice-of-Customer evidence.
Do NOT propose a feature or solution. The sequence is evidence -> understand -> validate -> solution later.
Preserve uncertainty and use only the supplied aggregate and excerpts.
Aggregate: {problem_brief}
Evidence excerpts: {evidence_examples}
"""
    return _parse_json(_generate(prompt,TICKET_SCHEMA))
