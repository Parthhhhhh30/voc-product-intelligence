import ai_layer

def test_generate_uses_header_and_low_thinking(monkeypatch):
    captured={}
    class Response:
        status_code=200
        def raise_for_status(self): pass
        def json(self): return {"candidates":[{"content":{"parts":[{"text":"ok"}]}}]}
    def fake_post(url,headers=None,json=None,timeout=None):
        captured.update(url=url,headers=headers,json=json,timeout=timeout)
        return Response()
    monkeypatch.setenv("GEMINI_API_KEY","test-key")
    monkeypatch.setattr(ai_layer.requests,"post",fake_post)
    assert ai_layer._generate("hello")=="ok"
    assert captured["headers"]["x-goog-api-key"]=="test-key"
    assert captured["json"]["generationConfig"]["thinkingConfig"]["thinkingLevel"]=="low"

def test_retry_503_then_success(monkeypatch):
    calls={"n":0}
    class Response:
        def __init__(self,status): self.status_code=status
        def raise_for_status(self): pass
        def json(self): return {"candidates":[{"content":{"parts":[{"text":"ok"}]}}]}
    def fake_post(*args,**kwargs):
        calls["n"]+=1
        return Response(503 if calls["n"]<3 else 200)
    monkeypatch.setenv("GEMINI_API_KEY","test-key")
    monkeypatch.setattr(ai_layer.requests,"post",fake_post)
    monkeypatch.setattr(ai_layer.time,"sleep",lambda *_:None)
    assert ai_layer._generate("hello")=="ok"
    assert calls["n"]==3

def test_ticket_fallback_preserves_validation(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY",raising=False)
    brief={"problem":"x","evidence_count":5,"evidence_share":5/30,"impact_reason":"Delayed activation","what_we_do_not_know_yet":"Cause unknown","suggested_next_step":"Observe and validate before proposing a solution."}
    ticket=ai_layer.draft_product_ticket(brief,["evidence"])
    assert "validate" in ticket["suggested_next_step"].lower()
