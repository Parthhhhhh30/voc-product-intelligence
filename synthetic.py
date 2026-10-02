from __future__ import annotations

import pandas as pd

THEME_DATA = {
    "Onboarding configuration unclear": {
        "impact":"High",
        "reason":"Can delay setup, activation or confidence in launch readiness.",
        "texts":[
            "The team was not sure which configuration choices had to be completed before launch, so we needed a second call.",
            "The checklist says configuration is complete, but staff still do not know whether every required option has been reviewed.",
            "We delayed activation because nobody was confident the original setup had covered all required workflow choices.",
            "After the setup call the practice manager could not tell what was still outstanding.",
            "Could you confirm which configuration items are mandatory? We have paused the rollout.",
            "The product is live, but we discovered one setup choice was missed and now the team is checking what else was skipped.",
            "We need a clearer way to know when configuration is actually finished rather than relying on memory.",
            "Activation is waiting because we cannot tell whether the current configuration is ready to sign off.",
        ],
    },
    "Staff communication uncertainty": {
        "impact":"Medium",
        "reason":"Creates inconsistent explanations and can slow staff confidence during adoption.",
        "texts":[
            "Reception staff understand the workflow internally but are unsure how to explain Navigator to patients in one simple sentence.",
            "Different staff are describing Navigator differently and patients are getting inconsistent explanations.",
            "The team asked what they should say when a patient questions why the booking route looks different.",
            "Newer reception staff do not know how to introduce the workflow without over-explaining.",
            "We need consistent patient-facing language instead of each receptionist improvising their own explanation.",
            "Usage is increasing, but staff still say the hardest part is explaining the Navigator workflow clearly.",
        ],
    },
    "Appointment availability configuration": {
        "impact":"High",
        "reason":"Can block or delay activation and create manual verification work.",
        "texts":[
            "We are not sure which appointment types should be exposed and which should remain unavailable during rollout.",
            "The availability settings look correct, but the team cannot tell why one service is not appearing as expected.",
            "Staff are checking appointment availability manually because they do not fully trust the configuration.",
            "The practice needs clearer guidance on how availability rules should be configured across appointment types.",
            "We paused one appointment route because we cannot validate that the availability configuration matches the intended workflow.",
        ],
    },
    "Reporting / value visibility": {
        "impact":"Medium",
        "reason":"Makes it harder to evidence outcomes and support retention or expansion decisions.",
        "texts":[
            "We can see staff are using the product but cannot easily show whether it is improving the agreed operational outcome.",
            "Usage alone is not enough for our internal review; we need a simple before-and-after view.",
            "The team wants a clearer way to decide whether the workflow is actually delivering value.",
            "We are due to review the rollout but do not have one place bringing together adoption and the operational measure we agreed.",
        ],
    },
    "Workflow handoff confusion": {
        "impact":"Medium",
        "reason":"Creates ownership gaps and avoidable delay between onboarding, activation and support.",
        "texts":[
            "The project lead thought reception owned the next step, while reception thought it was waiting on the implementation contact.",
            "The issue sat for two days because the practice and onboarding contact each thought the other side was taking the next action.",
            "When something falls between onboarding and normal support the team is unsure who owns it.",
            "We need clearer ownership when the implementation call ends and the practice moves into normal usage.",
        ],
    },
    "Support escalation unclear": {
        "impact":"High",
        "reason":"Can extend time-to-resolution when an operational issue needs escalation.",
        "texts":[
            "When the issue blocked today's workflow we did not know which route to use for urgent escalation or what evidence to include.",
            "The first support message lacked the details needed and we lost time going back and forth.",
            "Staff know where to ask for help, but they are unclear what counts as urgent and who should own escalation inside the practice.",
        ],
    },
}

STAGE_CYCLE=("Onboarding","Activation","Early adoption","Value review","Support")
CHANNEL_CYCLE=("Onboarding call","Support message","Customer check-in")

def feedback_records()->pd.DataFrame:
    rows=[]
    i=1
    for theme,info in THEME_DATA.items():
        for j,text in enumerate(info["texts"]):
            stage = "Support" if theme=="Support escalation unclear" else STAGE_CYCLE[j % len(STAGE_CYCLE)]
            rows.append({
                "feedback_id":f"VOC-{i:03d}",
                "account_id":f"DEMO-{i:02d}",
                "channel":CHANNEL_CYCLE[j % len(CHANNEL_CYCLE)],
                "workflow_stage":stage,
                "date":pd.Timestamp("2026-09-01")+pd.Timedelta(days=i-1),
                "text":text,
                "reference_theme":theme,
                "reference_impact":info["impact"],
            })
            i+=1
    return pd.DataFrame(rows)

def reviewed_extractions()->pd.DataFrame:
    source=feedback_records()
    out=source.rename(columns={"reference_theme":"theme","reference_impact":"impact_level"}).copy()
    out["problem"]=out["theme"]
    out["evidence"]=out["text"]
    out["impact_reason"]=out["theme"].map({k:v["reason"] for k,v in THEME_DATA.items()})
    out["confidence"]="High"
    out["review_status"]="Reviewed demo annotation"
    return out
