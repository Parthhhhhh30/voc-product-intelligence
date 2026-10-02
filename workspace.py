import html
import streamlit as st

from ai_layer import analyze_feedback, available as ai_available, draft_product_ticket
from analysis_engine import aggregate_themes, build_problem_brief, channel_distribution, stage_distribution, theme_evidence
from synthetic import feedback_records, reviewed_extractions
from taxonomy import IMPACT_LEVELS, THEMES, WORKFLOW_STAGES, theme_definition

STYLE="""
<style>
.stApp{background:#f6f7f6}.block-container{max-width:1380px;padding-top:1rem}
[data-testid="stSidebar"]{display:none}[data-testid="stHeader"]{background:transparent}
.top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e3e7e5;padding:.4rem 0 1rem;margin-bottom:1rem}
.brand{font-weight:800;font-size:1.05rem}.sub,.muted{color:#6d7471;font-size:.8rem}.title{font-size:2rem;font-weight:800;letter-spacing:-.03em}.copy{color:#6d7471;max-width:850px;margin:.4rem 0 1.1rem}
.card{background:white;border:1px solid #e3e7e5;border-radius:12px;padding:1rem;margin-bottom:.65rem}.quote{border-left:3px solid #cfd8d4;background:#fafbfa;padding:.7rem .8rem;border-radius:0 8px 8px 0}
.pill{display:inline-block;border-radius:999px;padding:.22rem .55rem;font-size:.72rem;font-weight:700;background:#edf3f7;margin:.3rem .25rem 0 0}
.high{background:#faecea;color:#8c403d}.medium{background:#f8f1df;color:#8b651c}.low{background:#eaf3ef;color:#28614f}
</style>
"""

def safe(x): return html.escape(str("" if x is None else x))
def pill(x,t=""): return f'<span class="pill {t}">{safe(x)}</span>'
def tone(x): return {"High":"high","Medium":"medium","Low":"low"}.get(str(x),"")
def header(title,copy):
    st.markdown(f'<div class="title">{safe(title)}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="copy">{safe(copy)}</div>',unsafe_allow_html=True)

def init():
    st.session_state.setdefault("ai_candidates",{})
    st.session_state.setdefault("overrides",{})
    st.session_state.setdefault("tickets",{})

def reviewed():
    data=reviewed_extractions().copy()
    for fid,vals in st.session_state.overrides.items():
        mask=data.feedback_id==fid
        for k,v in vals.items():
            if k in data.columns: data.loc[mask,k]=v
        data.loc[mask,"review_status"]="Human-reviewed live extraction"
    return data

def inbox():
    header("Feedback review inbox","Read source evidence first. AI proposes a structured extraction; a person edits or approves it before it affects product intelligence.")
    fb=feedback_records(); rev=reviewed()
    a,b,c=st.columns(3)
    with a: channel=st.selectbox("Channel",["All"]+sorted(fb.channel.unique()))
    with b: stage=st.selectbox("Workflow stage",["All"]+list(WORKFLOW_STAGES))
    with c: query=st.text_input("Search")
    view=fb.copy()
    if channel!="All": view=view[view.channel==channel]
    if stage!="All": view=view[view.workflow_stage==stage]
    if query: view=view[view.text.str.contains(query,case=False,na=False)|view.account_id.str.contains(query,case=False,na=False)]
    if view.empty: st.info("No matches."); return
    left,mid,right=st.columns([.7,1.15,1.1],gap="large")
    with left:
        fid=st.radio("Feedback",view.feedback_id.tolist(),format_func=lambda x:f"{x} · {view.loc[view.feedback_id==x,'account_id'].iloc[0]}",label_visibility="collapsed")
    row=fb[fb.feedback_id==fid].iloc[0]; cur=rev[rev.feedback_id==fid].iloc[0]
    with mid:
        st.markdown(f'<div class="card"><div class="muted">{safe(row.channel)} · {safe(row.workflow_stage)} · {safe(row.date.date())}</div><h3>{safe(row.account_id)}</h3><div class="quote">{safe(row.text)}</div></div>',unsafe_allow_html=True)
        st.caption("Synthetic feedback. No patient-level information.")
    with right:
        if st.button("Run live AI extraction",type="primary",use_container_width=True):
            try: st.session_state.ai_candidates[fid]=analyze_feedback(row.text,row.channel,row.workflow_stage)
            except Exception as exc: st.error(f"Analysis service error: {exc}")
        base=st.session_state.ai_candidates.get(fid) or cur.to_dict()
        st.caption("Live AI candidate" if fid in st.session_state.ai_candidates else "Reviewed demo annotation")
        with st.form(f"review-{fid}"):
            problem=st.text_area("Problem",str(base["problem"]))
            theme=st.selectbox("Theme",list(THEMES),index=list(THEMES).index(base["theme"]))
            wf=st.selectbox("Workflow stage",list(WORKFLOW_STAGES),index=list(WORKFLOW_STAGES).index(base["workflow_stage"]))
            impact=st.selectbox("Operational impact",list(IMPACT_LEVELS),index=list(IMPACT_LEVELS).index(base["impact_level"]))
            reason=st.text_area("Impact reason",str(base["impact_reason"]))
            evidence=st.text_area("Evidence",str(base["evidence"]))
            if st.form_submit_button("Approve into reviewed set",type="primary",use_container_width=True):
                st.session_state.overrides[fid]={"problem":problem,"theme":theme,"workflow_stage":wf,"impact_level":impact,"impact_reason":reason,"evidence":evidence}
                st.success("Approved for this session.")
        st.caption("No CRM or backlog is written automatically.")

def board():
    header("Theme board","Frequency and impact stay visible separately. Attention bands use explicit rules, not a hidden AI priority score.")
    themes=aggregate_themes(reviewed(),total_conversations=30)
    cols=st.columns(3,gap="large")
    for col,band in zip(cols,["High attention","Investigate","Monitor"]):
        with col:
            st.subheader(band)
            for r in themes[themes.attention_band==band].itertuples():
                st.markdown(f'<div class="card"><strong>{safe(r.theme)}</strong><div class="muted">{r.conversation_count} conversations · {r.conversation_share:.0%}</div>{pill(r.impact_level+" impact",tone(r.impact_level))}</div>',unsafe_allow_html=True)
    st.caption("High attention: high impact with ≥3 conversations, or ≥20% of sample. Investigate: ≥3 conversations or high impact.")

def evidence():
    header("Theme evidence room","Inspect every reviewed conversation behind a recurring theme before proposing a product response.")
    rev=reviewed(); themes=aggregate_themes(rev)
    theme=st.selectbox("Theme",themes.theme.tolist())
    s=themes[themes.theme==theme].iloc[0]; ev=theme_evidence(rev,theme)
    st.markdown(f'<div class="card"><h3>{safe(theme)}</h3><div class="muted">{safe(theme_definition(theme))}</div>{pill(f"{s.conversation_count} conversations")}{pill(f"{s.conversation_share:.0%} of sample")}{pill(s.impact_level+" impact",tone(s.impact_level))}</div>',unsafe_allow_html=True)
    l,r=st.columns([1.2,.8],gap="large")
    with l:
        for x in ev.itertuples():
            st.markdown(f'<div class="card"><strong>{safe(x.feedback_id)} · {safe(x.account_id)}</strong><div class="muted">{safe(x.channel)} · {safe(x.workflow_stage)}</div><div class="quote">{safe(x.evidence)}</div></div>',unsafe_allow_html=True)
    with r:
        st.dataframe(stage_distribution(rev,theme),hide_index=True,use_container_width=True)
        st.dataframe(channel_distribution(rev,theme),hide_index=True,use_container_width=True)
        st.info("Validation: confirm same underlying problem, observe workflow, check prevalence beyond sample, define evidence that would disconfirm the interpretation.")

def briefs():
    header("Problem briefs","Convert reviewed evidence into a product problem brief. The system deliberately has no recommended-feature field.")
    rev=reviewed(); themes=aggregate_themes(rev)
    theme=st.selectbox("Theme",themes.theme.tolist(),key="brief-theme")
    brief=build_problem_brief(rev,theme); ev=theme_evidence(rev,theme)
    l,r=st.columns(2,gap="large")
    with l:
        st.markdown(f'<div class="card"><h3>{safe(theme)}</h3><p><strong>{brief["evidence_count"]}/30 conversations ({brief["evidence_share"]:.0%})</strong></p>{pill(brief["impact_level"]+" impact",tone(brief["impact_level"]))}{pill(brief["status"])}</div>',unsafe_allow_html=True)
        st.write("**Impact:**",brief["impact_reason"])
        st.write("**Unknowns:**",brief["what_we_do_not_know_yet"])
        st.write("**Next validation step:**",brief["suggested_next_step"])
        if st.button("Draft product problem ticket",type="primary",use_container_width=True):
            try: st.session_state.tickets[theme]=draft_product_ticket(brief,ev.evidence.astype(str).head(5).tolist())
            except Exception as exc: st.error(f"Drafting service error: {exc}")
    with r:
        ticket=st.session_state.tickets.get(theme)
        if not ticket: st.info("No draft yet. AI only formats reviewed evidence.")
        else:
            for label,key in [("Problem","problem"),("Evidence","evidence"),("Operational impact","operational_impact"),("What we do not know yet","what_we_do_not_know_yet"),("Suggested next step","suggested_next_step")]:
                st.markdown(f"**{label}**"); st.write(ticket.get(key,""))
            st.caption("Human review required. Solution discovery starts only after validation.")

def method():
    header("Method & safeguards","AI helps with scale; deterministic logic owns aggregation; humans own product judgement.")
    st.markdown('<div class="card"><strong>Feedback → AI candidate → human review → deterministic themes → evidence + impact → problem brief → AI formatting → human validation → solution discovery later</strong></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    with a: st.subheader("AI"); st.write("Extracts one problem candidate, maps controlled taxonomy, drafts evidence-led tickets.")
    with b: st.subheader("Deterministic"); st.write("Counts themes, calculates shares, aggregates impact, assigns transparent attention bands.")
    with c: st.subheader("Human"); st.write("Approves extraction, corrects taxonomy, judges impact, prioritises work, validates causes and solutions.")
    st.warning("Demo uses 30 synthetic B2B conversations only. No patient data, clinical data, real Healthtech-1 data or real backlog.")

def render_app():
    init(); st.markdown(STYLE,unsafe_allow_html=True)
    st.markdown(f'<div class="top"><div><div class="brand">VOC Product Intelligence Engine</div><div class="sub">Evidence-led customer research workflow</div></div><div class="meta">Independent portfolio prototype<br>{"Live AI connected" if ai_available() else "Local demo mode"}</div></div>',unsafe_allow_html=True)
    page=st.segmented_control("Workspace",["Inbox","Theme board","Evidence","Problem briefs","Method"],default="Inbox",label_visibility="collapsed") or "Inbox"
    {"Inbox":inbox,"Theme board":board,"Evidence":evidence,"Problem briefs":briefs,"Method":method}[page]()
    st.divider(); st.caption("Independent portfolio prototype. No affiliation with Healthtech-1. No automated external actions.")
