from __future__ import annotations

THEMES = (
    "Onboarding configuration unclear",
    "Staff communication uncertainty",
    "Appointment availability configuration",
    "Reporting / value visibility",
    "Workflow handoff confusion",
    "Support escalation unclear",
    "Other / needs review",
)
WORKFLOW_STAGES = ("Pre-onboarding","Onboarding","Activation","Early adoption","Value review","Support")
IMPACT_LEVELS = ("Low","Medium","High")
CONFIDENCE_LEVELS = ("Low","Medium","High")
CHANNELS = ("Onboarding call","Support message","Customer check-in")
IMPACT_WEIGHT = {"Low":1,"Medium":2,"High":3}

DEFINITIONS = {
    "Onboarding configuration unclear":"Setup or configuration steps are unclear enough to slow onboarding or require repeated help.",
    "Staff communication uncertainty":"Practice staff are unsure how to explain the workflow or product to patients or colleagues.",
    "Appointment availability configuration":"Appointment or service availability settings are difficult to configure or validate.",
    "Reporting / value visibility":"The customer cannot easily see or evidence adoption, usage or operational value.",
    "Workflow handoff confusion":"Ownership or handoffs between people, teams or workflow stages are unclear.",
    "Support escalation unclear":"The customer is unsure how to escalate an issue or what information support needs.",
    "Other / needs review":"The feedback does not cleanly match the controlled taxonomy and should be reviewed manually.",
}

def theme_definition(theme: str) -> str:
    return DEFINITIONS[theme]
