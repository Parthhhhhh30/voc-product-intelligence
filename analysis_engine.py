from __future__ import annotations

import pandas as pd
from taxonomy import IMPACT_WEIGHT

def attention_band(conversation_count:int, conversation_share:float, impact_level:str)->str:
    if (impact_level=="High" and conversation_count>=3) or conversation_share>=0.20:
        return "High attention"
    if conversation_count>=3 or impact_level=="High":
        return "Investigate"
    return "Monitor"

def aggregate_themes(extractions:pd.DataFrame,total_conversations:int|None=None)->pd.DataFrame:
    required={"feedback_id","theme","impact_level","workflow_stage","channel"}
    missing=required.difference(extractions.columns)
    if missing:
        raise ValueError(f"Missing extraction columns: {sorted(missing)}")
    total_conversations=total_conversations or int(extractions.feedback_id.nunique())
    if total_conversations<=0:
        raise ValueError("total_conversations must be positive")
    rows=[]
    for theme,g in extractions.groupby("theme",sort=False):
        count=int(g.feedback_id.nunique())
        share=count/total_conversations
        impact=max(g.impact_level,key=lambda x:IMPACT_WEIGHT[x])
        rows.append({
            "theme":theme,"conversation_count":count,"conversation_share":share,
            "impact_level":impact,"attention_band":attention_band(count,share,impact),
            "affected_stages":tuple(sorted(set(g.workflow_stage))),
            "affected_channels":tuple(sorted(set(g.channel))),
        })
    result=pd.DataFrame(rows)
    if result.empty:
        return result
    order={"High attention":0,"Investigate":1,"Monitor":2}
    result["_band"]=result.attention_band.map(order)
    result["_impact"]=result.impact_level.map(IMPACT_WEIGHT)
    return result.sort_values(["_band","conversation_count","_impact","theme"],ascending=[True,False,False,True]).drop(columns=["_band","_impact"]).reset_index(drop=True)

def theme_evidence(extractions:pd.DataFrame,theme:str)->pd.DataFrame:
    return extractions[extractions.theme==theme].sort_values(["date","feedback_id"]).reset_index(drop=True)

def stage_distribution(extractions:pd.DataFrame,theme:str)->pd.DataFrame:
    x=theme_evidence(extractions,theme).groupby("workflow_stage").feedback_id.nunique().sort_values(ascending=False)
    return x.rename("conversations").reset_index()

def channel_distribution(extractions:pd.DataFrame,theme:str)->pd.DataFrame:
    x=theme_evidence(extractions,theme).groupby("channel").feedback_id.nunique().sort_values(ascending=False)
    return x.rename("conversations").reset_index()

def build_problem_brief(extractions:pd.DataFrame,theme:str)->dict:
    summary=aggregate_themes(extractions)
    row=summary[summary.theme==theme]
    if row.empty:
        raise ValueError(f"Unknown theme: {theme}")
    row=row.iloc[0]
    evidence=theme_evidence(extractions,theme)
    reasons=[x for x in evidence.impact_reason.dropna().astype(str).unique() if x]
    return {
        "theme":theme,"problem":theme,
        "evidence_count":int(row.conversation_count),"evidence_share":float(row.conversation_share),
        "impact_level":row.impact_level,
        "impact_reason":reasons[0] if reasons else "Needs validation.",
        "workflow_stages":list(row.affected_stages),"channels":list(row.affected_channels),
        "what_we_do_not_know_yet":"The underlying cause, prevalence outside this sample and best intervention remain unvalidated.",
        "suggested_next_step":"Observe affected workflows, confirm the problem with customers, and validate the underlying cause before proposing a solution.",
        "status":"Needs validation",
    }
