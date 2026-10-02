import pandas as pd
from analysis_engine import aggregate_themes, attention_band, build_problem_brief
from synthetic import reviewed_extractions

def test_attention_band_rules():
    assert attention_band(3,.10,"High")=="High attention"
    assert attention_band(6,.20,"Medium")=="High attention"
    assert attention_band(3,.10,"Medium")=="Investigate"
    assert attention_band(1,.03,"Low")=="Monitor"

def test_theme_aggregation_matches_demo():
    summary=aggregate_themes(reviewed_extractions(),30)
    row=summary[summary.theme=="Onboarding configuration unclear"].iloc[0]
    assert row.conversation_count==8
    assert round(row.conversation_share,3)==round(8/30,3)
    assert row.impact_level=="High"

def test_problem_brief_keeps_validation_boundary():
    brief=build_problem_brief(reviewed_extractions(),"Appointment availability configuration")
    assert brief["evidence_count"]==5
    assert brief["status"]=="Needs validation"
    assert "validate" in brief["suggested_next_step"].lower()
    assert "build" not in brief["suggested_next_step"].lower()

def test_missing_columns_fail():
    try:
        aggregate_themes(pd.DataFrame({"theme":["x"]}))
    except ValueError as exc:
        assert "Missing extraction columns" in str(exc)
    else:
        raise AssertionError("Missing data contract should fail")
