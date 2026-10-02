import json

import ai_layer


def test_generate_uses_header_and_low_thinking(monkeypatch):
    captured = {}

    class Response:
        status_code = 200
        text = ""

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(url=url, headers=headers, json=json, timeout=timeout)
        return Response()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_layer.requests, "post", fake_post)

    assert ai_layer._generate("hello") == "ok"
    assert captured["headers"]["x-goog-api-key"] == "test-key"
    assert captured["json"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "low"


def test_retry_503_then_success(monkeypatch):
    calls = {"n": 0}

    class Response:
        text = ""

        def __init__(self, status):
            self.status_code = status

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        return Response(503 if calls["n"] < 3 else 200)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_layer.requests, "post", fake_post)
    monkeypatch.setattr(ai_layer.time, "sleep", lambda *_: None)

    assert ai_layer._generate("hello") == "ok"
    assert calls["n"] == 3


def test_structured_400_falls_back_to_legacy_schema(monkeypatch):
    payloads = []

    class Response:
        def __init__(self, status, output="", text=""):
            self.status_code = status
            self._output = output
            self.text = text

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": self._output}]}}
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        payloads.append(json)
        config = json["generationConfig"]
        if "responseFormat" in config:
            return Response(400, text='{"error":{"message":"unsupported envelope"}}')
        return Response(200, output='{"x":"ok"}')

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_layer.requests, "post", fake_post)

    out = ai_layer._generate(
        "return json",
        {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
    )

    assert json.loads(out) == {"x": "ok"}
    assert "responseFormat" in payloads[0]["generationConfig"]
    assert payloads[1]["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseSchema" in payloads[1]["generationConfig"]


def test_structured_double_400_falls_back_to_prompt_json(monkeypatch):
    payloads = []

    class Response:
        def __init__(self, status, output="", text=""):
            self.status_code = status
            self._output = output
            self.text = text

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": self._output}]}}
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        payloads.append(json)
        config = json["generationConfig"]
        if "responseFormat" in config or "responseSchema" in config:
            return Response(400, text="schema envelope rejected")
        return Response(200, output='{"x":"ok"}')

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_layer.requests, "post", fake_post)

    out = ai_layer._generate(
        "return json",
        {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
    )

    assert json.loads(out) == {"x": "ok"}
    assert len(payloads) == 3
    assert "Return JSON only" in payloads[2]["contents"][0]["parts"][0]["text"]


def test_extraction_validator_rejects_unknown_theme():
    data = {
        "problem": "x",
        "theme": "Invented theme",
        "workflow_stage": "Onboarding",
        "impact_level": "Medium",
        "impact_reason": "x",
        "evidence": "x",
        "confidence": "High",
        "needs_human_review": False,
    }
    try:
        ai_layer._validate_extraction(data)
    except ValueError as exc:
        assert "unknown theme" in str(exc).lower()
    else:
        raise AssertionError("unknown theme must be rejected")


def test_ticket_validator_rejects_solution_field():
    data = {
        "problem": "x",
        "evidence": "x",
        "operational_impact": "x",
        "what_we_do_not_know_yet": "x",
        "suggested_next_step": "validate",
        "recommended_feature": "build something",
    }
    try:
        ai_layer._validate_ticket(data)
    except ValueError as exc:
        assert "problem-before-solution" in str(exc)
    else:
        raise AssertionError("solution field must be rejected")


def test_ticket_fallback_preserves_validation(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    brief = {
        "problem": "x",
        "evidence_count": 5,
        "evidence_share": 5 / 30,
        "impact_reason": "Delayed activation",
        "what_we_do_not_know_yet": "Cause unknown",
        "suggested_next_step": "Observe and validate before proposing a solution.",
    }
    ticket = ai_layer.draft_product_ticket(brief, ["evidence"])
    assert "validate" in ticket["suggested_next_step"].lower()
