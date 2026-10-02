from __future__ import annotations

import html

import streamlit as st

from ai_layer import analyze_feedback, available as ai_available, draft_product_ticket
from analysis_engine import (
    aggregate_themes,
    build_problem_brief,
    channel_distribution,
    stage_distribution,
    theme_evidence,
)
from synthetic import feedback_records, reviewed_extractions
from taxonomy import IMPACT_LEVELS, THEMES, WORKFLOW_STAGES, theme_definition


STYLE = """
<style>
:root{
  --navy:#102033; --navy2:#172b43; --ink:#17202a; --muted:#6e746f;
  --paper:#fffdf8; --canvas:#f3efe7; --line:#d8d0c3; --coral:#e56f51;
  --teal:#2e7b74; --mustard:#c99a43; --rose:#a84f55; --cream:#ebe4d7;
}
.stApp{background:var(--canvas)}
.block-container{max-width:1240px;padding-top:1.25rem;padding-bottom:4rem}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:var(--navy);border-right:0}
[data-testid="stSidebar"] > div:first-child{padding-top:1.3rem}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#f5efe4!important}
[data-testid="stSidebar"] [role="radiogroup"] label{
  padding:.62rem .7rem;border-radius:8px;margin:.15rem 0;border:1px solid transparent;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.07)}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.13)}
h1,h2,h3,p,label,li{color:var(--ink)}
.hero{padding:.45rem 0 1rem;border-bottom:1px solid var(--line);margin-bottom:1.4rem}
.hero-top{display:flex;justify-content:space-between;align-items:flex-start;gap:2rem}
.eyebrow{font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;color:var(--coral)}
.hero-title{font-family:Georgia,'Times New Roman',serif;font-size:2.8rem;line-height:1.03;letter-spacing:-.035em;margin:.35rem 0 .45rem;color:var(--navy)}
.hero-copy{max-width:760px;color:var(--muted);font-size:.97rem;line-height:1.55}
.hero-status{font-size:.76rem;text-align:right;color:var(--muted);min-width:180px}
.stat-ribbon{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:1px solid var(--line);background:var(--paper);margin:1rem 0 1.5rem}
.stat-cell{padding:.85rem 1rem;border-right:1px solid var(--line)}.stat-cell:last-child{border-right:none}
.stat-value{font-family:Georgia,'Times New Roman',serif;font-size:1.55rem;color:var(--navy);font-weight:700}
.stat-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted)}
.section-no{font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;color:var(--coral);font-weight:800}
.page-title{font-family:Georgia,'Times New Roman',serif;font-size:2rem;color:var(--navy);margin:.22rem 0 .25rem}
.page-copy{color:var(--muted);max-width:840px;margin-bottom:1.2rem;line-height:1.5}
.filter-strip{background:var(--cream);border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:.65rem .85rem;margin-bottom:1rem}
.paper{background:var(--paper);border:1px solid var(--line);box-shadow:0 8px 26px rgba(31,38,45,.06);padding:1.4rem 1.45rem}
.paper-meta{font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.paper-id{font-family:Georgia,'Times New Roman',serif;font-size:1.35rem;font-weight:700;color:var(--navy);margin:.25rem 0 1rem}
.transcript{font-family:Georgia,'Times New Roman',serif;font-size:1.13rem;line-height:1.72;color:#28313a;border-left:4px solid var(--coral);padding-left:1rem}
.margin-note{font-size:.75rem;color:var(--muted);padding-top:.8rem}
.desk{background:#e9e3d7;border:1px solid #d4cbbb;padding:1rem}
.desk-title{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:var(--navy)}
.signal-row{display:grid;grid-template-columns:58px 1.35fr 2.2fr 110px;align-items:center;gap:.8rem;border-top:1px solid var(--line);padding:.85rem .2rem}
.signal-row:last-child{border-bottom:1px solid var(--line)}
.signal-count{font-family:Georgia,'Times New Roman',serif;font-size:1.8rem;color:var(--navy);font-weight:700}
.signal-name{font-weight:750;color:var(--ink)}
.signal-meta{font-size:.74rem;color:var(--muted);margin-top:.2rem}
.bar-track{height:10px;background:#ddd5c9;border-radius:999px;overflow:hidden}
.bar-fill{height:100%;background:var(--coral);border-radius:999px}
.band{font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;font-weight:800;padding:.28rem .48rem;border:1px solid var(--line);background:var(--paper);text-align:center}
.band.high{border-color:#d9b0a8;color:#8f4438;background:#f6e3df}
.band.investigate{border-color:#decaa1;color:#7b601e;background:#f7edcf}
.band.monitor{border-color:#aacbc6;color:#26645e;background:#e2f1ee}
.impact{display:inline-block;font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;margin-top:.25rem}
.impact.High{color:var(--rose)}.impact.Medium{color:#8a641e}.impact.Low{color:var(--teal)}
.ledger-head{display:grid;grid-template-columns:60px 120px 1fr;gap:1rem;padding:.55rem .3rem;border-bottom:2px solid var(--navy);font-size:.66rem;text-transform:uppercase;letter-spacing:.1em;font-weight:800;color:var(--navy)}
.ledger-row{display:grid;grid-template-columns:60px 120px 1fr;gap:1rem;padding:1rem .3rem;border-bottom:1px solid var(--line)}
.ledger-no{font-family:Georgia,'Times New Roman',serif;font-size:1.25rem;color:var(--coral)}
.ledger-meta{font-size:.72rem;color:var(--muted);line-height:1.5}
.ledger-quote{font-family:Georgia,'Times New Roman',serif;line-height:1.55;color:#2c343a}
.memo{background:var(--paper);border:1px solid var(--line);box-shadow:0 10px 30px rgba(31,38,45,.07);padding:1.5rem 1.65rem;min-height:430px}
.memo-top{display:flex;justify-content:space-between;border-bottom:2px solid var(--navy);padding-bottom:.65rem;margin-bottom:1rem}
.memo-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.13em;font-weight:800;color:var(--coral)}
.memo-state{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.memo h4{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:1.1rem 0 .25rem}
.memo p{font-family:Georgia,'Times New Roman',serif;line-height:1.55;margin:.1rem 0;color:#293139}
.contract{background:var(--navy);color:#f5efe4;padding:1.5rem;margin:.6rem 0 1.2rem}
.contract *{color:#f5efe4}
.contract-flow{font-family:Georgia,'Times New Roman',serif;font-size:1.28rem;line-height:1.55}
.callout{border-left:4px solid var(--mustard);background:#f2ead8;padding:.8rem .9rem;color:#564b37;font-size:.88rem}
.sidebar-brand{font-family:Georgia,'Times New Roman',serif;font-size:1.45rem;font-weight:700;color:#fff;margin-bottom:.2rem}
.sidebar-kicker{font-size:.64rem;letter-spacing:.16em;text-transform:uppercase;color:#e5a68f!important;font-weight:800}
.sidebar-small{font-size:.72rem;color:#bdc7d0!important;line-height:1.45}
div.stButton>button{border-radius:5px;font-weight:750;min-height:2.5rem;border:1px solid var(--navy)}
div.stButton>button[kind="primary"]{background:var(--navy);color:#fff}
.stTextInput input,.stSelectbox>div>div,.stTextArea textarea{border-radius:4px!important}
.stDataFrame{border:1px solid var(--line);background:var(--paper)}
@media(max-width:900px){
  .hero-top{display:block}.hero-status{text-align:left;margin-top:.8rem}.stat-ribbon{grid-template-columns:repeat(2,1fr)}
  .signal-row{grid-template-columns:50px 1fr}.signal-row .bar-track,.signal-row .band{grid-column:2}
  .ledger-head,.ledger-row{grid-template-columns:45px 1fr}.ledger-head>:nth-child(2),.ledger-row>:nth-child(2){display:none}
}
</style>
"""


def safe(value) -> str:
    return html.escape(str("" if value is None else value))


def init_state() -> None:
    st.session_state.setdefault("ai_candidates", {})
    st.session_state.setdefault("overrides", {})
    st.session_state.setdefault("tickets", {})


def reviewed_data():
    data = reviewed_extractions().copy()
    for feedback_id, values in st.session_state.overrides.items():
        mask = data.feedback_id == feedback_id
        for key, value in values.items():
            if key in data.columns:
                data.loc[mask, key] = value
        data.loc[mask, "review_status"] = "Human-reviewed live extraction"
    return data


def page_header(number: str, title: str, copy: str) -> None:
    st.markdown(f'<div class="section-no">{safe(number)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title">{safe(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-copy">{safe(copy)}</div>', unsafe_allow_html=True)


def sidebar_nav() -> str:
    with st.sidebar:
        st.markdown('<div class="sidebar-kicker">Product research studio</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-brand">VoC / Fieldnotes</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-small">Turn raw customer language into evidence-backed product questions — not instant feature ideas.</div>', unsafe_allow_html=True)
        st.divider()
        page = st.radio(
            "Navigate",
            ["Research desk", "Signal atlas", "Evidence ledger", "Problem memo", "Operating contract"],
            label_visibility="collapsed",
        )
        st.divider()
        st.markdown(
            '<div class="sidebar-small">30 synthetic conversations<br>6 recurring themes<br>No patient-level data<br>No automatic backlog writes</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="sidebar-small" style="margin-top:1rem">AI: {"connected" if ai_available() else "local demo mode"}</div>',
            unsafe_allow_html=True,
        )
    return page


def render_hero() -> None:
    st.markdown(
        f'''<div class="hero"><div class="hero-top"><div>
        <div class="eyebrow">Voice of customer / product intelligence</div>
        <div class="hero-title">Research the problem<br>before designing the answer.</div>
        <div class="hero-copy">A working research studio for reviewing customer conversations, finding recurring friction, tracing every theme back to source evidence, and drafting problem briefs that stop before feature selection.</div>
        </div><div class="hero-status">Independent portfolio prototype<br>{"Live Gemini extraction available" if ai_available() else "Deterministic demo mode"}<br>Human review required</div></div></div>''',
        unsafe_allow_html=True,
    )
    summary = aggregate_themes(reviewed_data(), total_conversations=30)
    high = int((summary.attention_band == "High attention").sum())
    st.markdown(
        f'''<div class="stat-ribbon">
        <div class="stat-cell"><div class="stat-value">30</div><div class="stat-label">conversations</div></div>
        <div class="stat-cell"><div class="stat-value">{len(summary)}</div><div class="stat-label">recurring themes</div></div>
        <div class="stat-cell"><div class="stat-value">{high}</div><div class="stat-label">high-attention themes</div></div>
        <div class="stat-cell"><div class="stat-value">0</div><div class="stat-label">features auto-recommended</div></div>
        </div>''',
        unsafe_allow_html=True,
    )


def render_research_desk() -> None:
    page_header(
        "01 / RESEARCH DESK",
        "Feedback review inbox",
        "The raw conversation stays visually dominant. AI can propose a structured interpretation, but only a reviewed extraction is allowed to influence the evidence set.",
    )
    feedback = feedback_records()
    reviewed = reviewed_data()

    st.markdown('<div class="filter-strip">FILTER THE FIELD NOTES</div>', unsafe_allow_html=True)
    a, b, c = st.columns([1, 1, 1.3])
    with a:
        channel = st.selectbox("Channel", ["All"] + sorted(feedback.channel.unique()), key="desk-channel")
    with b:
        stage = st.selectbox("Journey stage", ["All"] + list(WORKFLOW_STAGES), key="desk-stage")
    with c:
        query = st.text_input("Search", placeholder="Search text or demo account", key="desk-search")

    view = feedback.copy()
    if channel != "All":
        view = view[view.channel == channel]
    if stage != "All":
        view = view[view.workflow_stage == stage]
    if query:
        view = view[
            view.text.str.contains(query, case=False, na=False)
            | view.account_id.str.contains(query, case=False, na=False)
        ]
    if view.empty:
        st.info("No feedback matches the current filters.")
        return

    pick, transcript, analysis = st.columns([0.62, 1.35, 1.03], gap="large")
    with pick:
        st.markdown("**CONVERSATION INDEX**")
        feedback_id = st.selectbox(
            "Open note",
            view.feedback_id.tolist(),
            format_func=lambda x: f"{x} · {view.loc[view.feedback_id == x, 'account_id'].iloc[0]}",
            label_visibility="collapsed",
            key="desk-note",
        )
        st.caption(f"{len(view)} notes in this view")
        compact = view[["feedback_id", "channel", "workflow_stage"]].head(12)
        st.dataframe(compact, hide_index=True, use_container_width=True, height=330)

    row = feedback[feedback.feedback_id == feedback_id].iloc[0]
    current = reviewed[reviewed.feedback_id == feedback_id].iloc[0]

    with transcript:
        st.markdown(
            f'''<div class="paper">
            <div class="paper-meta">{safe(row.channel)} / {safe(row.workflow_stage)} / {safe(row.date.date())}</div>
            <div class="paper-id">{safe(row.feedback_id)} · {safe(row.account_id)}</div>
            <div class="transcript">{safe(row.text)}</div>
            <div class="margin-note">Synthetic research note. No patient-level or clinical information.</div>
            </div>''',
            unsafe_allow_html=True,
        )

    with analysis:
        st.markdown('<div class="desk-title">ANALYSIS DESK</div>', unsafe_allow_html=True)
        if st.button("Analyse this note", type="primary", use_container_width=True, key="analyse-note"):
            try:
                st.session_state.ai_candidates[feedback_id] = analyze_feedback(
                    row.text, row.channel, row.workflow_stage
                )
            except Exception as exc:
                st.error(f"Analysis service error: {exc}")

        candidate = st.session_state.ai_candidates.get(feedback_id)
        base = candidate or current.to_dict()
        st.caption("Live AI candidate" if candidate else "Reviewed demo annotation")

        with st.form(f"review-{feedback_id}"):
            problem = st.text_area("Problem statement", value=str(base["problem"]), height=88)
            theme = st.selectbox("Theme", list(THEMES), index=list(THEMES).index(base["theme"]))
            workflow_stage = st.selectbox(
                "Journey stage",
                list(WORKFLOW_STAGES),
                index=list(WORKFLOW_STAGES).index(base["workflow_stage"]),
            )
            impact = st.selectbox(
                "Operational impact",
                list(IMPACT_LEVELS),
                index=list(IMPACT_LEVELS).index(base["impact_level"]),
            )
            reason = st.text_area("Why this impact?", value=str(base["impact_reason"]), height=70)
            evidence = st.text_area("Evidence excerpt", value=str(base["evidence"]), height=82)
            if st.form_submit_button("Approve interpretation", type="primary", use_container_width=True):
                st.session_state.overrides[feedback_id] = {
                    "problem": problem,
                    "theme": theme,
                    "workflow_stage": workflow_stage,
                    "impact_level": impact,
                    "impact_reason": reason,
                    "evidence": evidence,
                    "confidence": str(base.get("confidence", "Medium")),
                }
                st.success("Approved into this session's reviewed evidence set.")
        st.caption("Approval changes analysis only for this session. Nothing is sent externally.")


def render_signal_atlas() -> None:
    page_header(
        "02 / SIGNAL ATLAS",
        "Recurring patterns, shown as evidence — not scores.",
        "Themes are ordered by explicit attention rules. The visual length represents conversation share only; operational impact stays separate so frequency cannot masquerade as importance.",
    )
    themes = aggregate_themes(reviewed_data(), total_conversations=30)

    for row in themes.itertuples():
        width = max(4, min(100, int(round(row.conversation_share * 100))))
        band_class = {
            "High attention": "high",
            "Investigate": "investigate",
            "Monitor": "monitor",
        }[row.attention_band]
        st.markdown(
            f'''<div class="signal-row">
            <div class="signal-count">{int(row.conversation_count)}</div>
            <div><div class="signal-name">{safe(row.theme)}</div>
            <div class="signal-meta">{row.conversation_share:.0%} of 30 conversations · <span class="impact {safe(row.impact_level)}">{safe(row.impact_level)} impact</span></div></div>
            <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
            <div class="band {band_class}">{safe(row.attention_band)}</div>
            </div>''',
            unsafe_allow_html=True,
        )

    st.markdown("### How to read the atlas")
    st.markdown(
        '<div class="callout"><strong>High attention</strong> = High impact with at least 3 conversations, or at least 20% of the sample. <strong>Investigate</strong> = at least 3 conversations, or High impact. <strong>Monitor</strong> = everything else. These are prototype decision rules, not company or NHS standards.</div>',
        unsafe_allow_html=True,
    )


def render_evidence_ledger() -> None:
    page_header(
        "03 / EVIDENCE LEDGER",
        "Trace a theme back to every supporting conversation.",
        "The ledger is the anti-hallucination layer: every aggregate theme can be audited against the exact reviewed evidence, channel and point in the customer journey.",
    )
    reviewed = reviewed_data()
    themes = aggregate_themes(reviewed)
    theme = st.selectbox("Open theme", themes.theme.tolist(), key="ledger-theme")
    summary = themes[themes.theme == theme].iloc[0]
    evidence = theme_evidence(reviewed, theme)

    st.markdown(
        f'''<div class="paper" style="margin-bottom:1rem">
        <div class="paper-meta">THEME DOSSIER</div>
        <div class="paper-id">{safe(theme)}</div>
        <div style="color:#6e746f">{safe(theme_definition(theme))}</div>
        <div style="margin-top:.75rem"><strong>{int(summary.conversation_count)} conversations</strong> · {summary.conversation_share:.0%} of sample · {safe(summary.impact_level)} operational impact</div>
        </div>''',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.35, 0.65], gap="large")
    with left:
        st.markdown('<div class="ledger-head"><div>Ref</div><div>Context</div><div>Reviewed evidence</div></div>', unsafe_allow_html=True)
        for i, row in enumerate(evidence.itertuples(), start=1):
            st.markdown(
                f'''<div class="ledger-row">
                <div class="ledger-no">{i:02d}</div>
                <div class="ledger-meta">{safe(row.feedback_id)}<br>{safe(row.channel)}<br>{safe(row.workflow_stage)}</div>
                <div class="ledger-quote">{safe(row.evidence)}</div>
                </div>''',
                unsafe_allow_html=True,
            )
    with right:
        st.markdown("#### Journey distribution")
        st.dataframe(stage_distribution(reviewed, theme), hide_index=True, use_container_width=True)
        st.markdown("#### Channel distribution")
        st.dataframe(channel_distribution(reviewed, theme), hide_index=True, use_container_width=True)
        st.markdown(
            '<div class="callout"><strong>Validation questions</strong><br>Is this the same underlying problem across accounts?<br>What workflow causes it?<br>Does it appear outside this sample?<br>What evidence would disconfirm the interpretation?</div>',
            unsafe_allow_html=True,
        )


def render_problem_memo() -> None:
    page_header(
        "04 / PROBLEM MEMO",
        "Write the problem down before discussing solutions.",
        "The memo turns reviewed evidence into a product-ready problem statement while deliberately omitting any field for a recommended feature.",
    )
    reviewed = reviewed_data()
    themes = aggregate_themes(reviewed)
    theme = st.selectbox("Research theme", themes.theme.tolist(), key="memo-theme")
    brief = build_problem_brief(reviewed, theme)
    evidence = theme_evidence(reviewed, theme)

    left, right = st.columns([0.92, 1.08], gap="large")
    with left:
        st.markdown(
            f'''<div class="memo">
            <div class="memo-top"><div class="memo-label">RESEARCH MEMO</div><div class="memo-state">{safe(brief["status"])}</div></div>
            <h4>Problem</h4><p>{safe(brief["problem"])}</p>
            <h4>Evidence</h4><p>{brief["evidence_count"]} of 30 reviewed conversations ({brief["evidence_share"]:.0%}).</p>
            <h4>Operational impact</h4><p>{safe(brief["impact_reason"])}</p>
            <h4>What we do not know yet</h4><p>{safe(brief["what_we_do_not_know_yet"])}</p>
            <h4>Next validation step</h4><p>{safe(brief["suggested_next_step"])}</p>
            </div>''',
            unsafe_allow_html=True,
        )
        if st.button("Draft structured product ticket", type="primary", use_container_width=True, key="memo-draft"):
            try:
                st.session_state.tickets[theme] = draft_product_ticket(
                    brief, evidence.evidence.astype(str).head(5).tolist()
                )
            except Exception as exc:
                st.error(f"Drafting service error: {exc}")

    with right:
        st.markdown("#### Draft for Product / Operations")
        ticket = st.session_state.tickets.get(theme)
        if ticket is None:
            st.markdown(
                '<div class="paper"><div class="paper-meta">NOT YET DRAFTED</div><div class="transcript" style="font-size:1rem">The evidence already exists. AI is optional here: it only turns the reviewed memo into a structured handoff.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'''<div class="paper">
                <div class="paper-meta">DRAFT · HUMAN REVIEW REQUIRED</div>
                <div class="paper-id">Product problem ticket</div>
                <strong>Problem</strong><p>{safe(ticket.get("problem",""))}</p>
                <strong>Evidence</strong><p>{safe(ticket.get("evidence",""))}</p>
                <strong>Operational impact</strong><p>{safe(ticket.get("operational_impact",""))}</p>
                <strong>What we do not know yet</strong><p>{safe(ticket.get("what_we_do_not_know_yet",""))}</p>
                <strong>Suggested next step</strong><p>{safe(ticket.get("suggested_next_step",""))}</p>
                </div>''',
                unsafe_allow_html=True,
            )
        st.markdown(
            '<div class="callout" style="margin-top:1rem"><strong>Design constraint:</strong> there is intentionally no “recommended feature” field. Product solutioning begins only after the problem has been validated.</div>',
            unsafe_allow_html=True,
        )


def render_operating_contract() -> None:
    page_header(
        "05 / OPERATING CONTRACT",
        "What the system is allowed to do — and what it is not.",
        "This boundary is part of the product, not a disclaimer added afterwards.",
    )
    st.markdown(
        '''<div class="contract">
        <div class="eyebrow" style="color:#e9a68f">THE DECISION CHAIN</div>
        <div class="contract-flow">Customer evidence → AI candidate → human review → deterministic aggregation → problem memo → AI formatting → human validation → solution discovery later.</div>
        </div>''',
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3, gap="large")
    with a:
        st.markdown("### AI may")
        st.write("Extract one problem candidate, map it to a controlled taxonomy, summarise evidence and draft a structured handoff.")
    with b:
        st.markdown("### Code owns")
        st.write("Counts, percentages, theme aggregation, evidence retrieval, stage/channel distributions and transparent attention rules.")
    with c:
        st.markdown("### Humans own")
        st.write("Approval, taxonomy correction, impact judgement, customer follow-up, backlog priority, causal validation and every solution decision.")

    st.markdown(
        '<div class="paper"><div class="paper-meta">DATA BOUNDARY</div><div class="paper-id">Synthetic B2B research set only</div><div>No patient names, NHS numbers, dates of birth, diagnoses, medications, clinical decisions, real Healthtech-1 calls or real customer backlog data are used.</div></div>',
        unsafe_allow_html=True,
    )


def render_app() -> None:
    init_state()
    st.markdown(STYLE, unsafe_allow_html=True)
    page = sidebar_nav()
    render_hero()

    {
        "Research desk": render_research_desk,
        "Signal atlas": render_signal_atlas,
        "Evidence ledger": render_evidence_ledger,
        "Problem memo": render_problem_memo,
        "Operating contract": render_operating_contract,
    }[page]()

    st.divider()
    st.caption(
        "Independent portfolio prototype. No affiliation with Healthtech-1. No automated external actions."
    )
