import httpx
import pytest

from app.config import get_settings
from app.services.ai_service import AIService, AIServiceError, _extract_json


@pytest.fixture()
def openrouter_env(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model:free")
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "")
    monkeypatch.setattr("time.sleep", lambda s: None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _response(status: int, json_body=None):
    return httpx.Response(status, json=json_body, request=httpx.Request("POST", "https://x"))


def test_openrouter_returns_message_content_and_sends_json_mode(openrouter_env, monkeypatch):
    seen = {}

    def fake_post(url, json, headers, timeout):
        seen.update(url=url, json=json, headers=headers)
        return _response(200, {"choices": [{"message": {"content": '{"ok": true}'}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    out = AIService()._call_model("hello")

    assert out == '{"ok": true}'
    assert seen["url"].endswith("/chat/completions")
    assert seen["json"]["model"] == "some/model:free"
    assert seen["json"]["response_format"] == {"type": "json_object"}
    assert seen["headers"]["Authorization"] == "Bearer test-key"


@pytest.mark.parametrize(
    "status,fragment",
    [(401, "credentials"), (402, "usage limit"), (404, "model is unavailable"), (429, "too many"), (503, "temporarily")],
)
def test_openrouter_http_errors_map_to_safe_messages(openrouter_env, monkeypatch, status, fragment):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _response(status, {"error": {"message": "secret detail"}}))
    with pytest.raises(AIServiceError) as exc:
        AIService()._call_model("x")
    assert fragment in str(exc.value)
    assert "secret detail" not in str(exc.value)


def test_openrouter_error_inside_200_is_reported(openrouter_env, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _response(200, {"error": {"code": 429, "message": "rate"}}))
    with pytest.raises(AIServiceError, match="too many"):
        AIService()._call_model("x")


def test_openrouter_timeout(openrouter_env, monkeypatch):
    def boom(*a, **k):
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(AIServiceError, match="too long"):
        AIService()._call_model("x")


def test_openrouter_missing_key_is_not_configured(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    get_settings.cache_clear()
    try:
        assert get_settings().has_ai_configured is False
        with pytest.raises(AIServiceError, match="credentials"):
            AIService()._call_model("x")
    finally:
        get_settings.cache_clear()


def test_extract_json_handles_prose_around_object():
    assert _extract_json('Sure! Here it is:\n{"a": 1}\nHope that helps') == '{"a": 1}'
    assert _extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_openrouter_falls_back_to_next_model_when_rate_limited(openrouter_env, monkeypatch):
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "backup/model:free")
    get_settings.cache_clear()
    tried = []

    def fake_post(url, json, headers, timeout):
        tried.append(json["model"])
        if json["model"] == "some/model:free":
            return _response(429, {"error": {"message": "limited"}})
        return _response(200, {"choices": [{"message": {"content": '{"ok": 1}'}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert AIService()._call_model("x") == '{"ok": 1}'
    assert tried == ["some/model:free", "some/model:free", "backup/model:free"]


def test_openrouter_all_models_limited_reports_rate_limit(openrouter_env, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _response(429, {"error": {}}))
    with pytest.raises(AIServiceError, match="too many"):
        AIService()._call_model("x")


def test_openrouter_empty_message_falls_back_to_next_model(openrouter_env, monkeypatch):
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "backup/model:free")
    get_settings.cache_clear()
    tried = []

    def fake_post(url, json, headers, timeout):
        tried.append(json["model"])
        content = "" if json["model"] == "some/model:free" else '{"ok": 2}'
        return _response(200, {"choices": [{"message": {"content": content}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert AIService()._call_model("x") == '{"ok": 2}'
    assert tried == ["some/model:free", "backup/model:free"]
