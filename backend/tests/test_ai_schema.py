import pytest
from pydantic import BaseModel

from app.services.ai_service import AIService, AIServiceError


class DummySchema(BaseModel):
    value: int


def test_generate_structured_returns_valid_response(monkeypatch):
    service = AIService()
    monkeypatch.setattr(service, "_call_model", lambda prompt: '{"value": 42}')

    result = service.generate_structured("prompt", DummySchema)

    assert result.value == 42


def test_generate_structured_strips_markdown_fences(monkeypatch):
    service = AIService()
    monkeypatch.setattr(service, "_call_model", lambda prompt: '```json\n{"value": 7}\n```')

    result = service.generate_structured("prompt", DummySchema)

    assert result.value == 7


def test_generate_structured_retries_once_on_invalid_json(monkeypatch):
    service = AIService()
    calls = {"count": 0}

    def flaky_call(prompt: str) -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            return "not json at all"
        return '{"value": 5}'

    monkeypatch.setattr(service, "_call_model", flaky_call)

    result = service.generate_structured("prompt", DummySchema)

    assert result.value == 5
    assert calls["count"] == 2


def test_generate_structured_fails_safely_on_malformed_structured_response(monkeypatch):
    """Valid JSON that doesn't match the schema should also trigger the retry path."""
    service = AIService()
    monkeypatch.setattr(service, "_call_model", lambda prompt: '{"unexpected_field": true}')

    with pytest.raises(AIServiceError):
        service.generate_structured("prompt", DummySchema)


def test_generate_structured_fails_safely_after_two_bad_responses(monkeypatch):
    service = AIService()
    monkeypatch.setattr(service, "_call_model", lambda prompt: "still not json")

    with pytest.raises(AIServiceError):
        service.generate_structured("prompt", DummySchema)


def test_get_client_raises_when_base_url_not_configured(monkeypatch):
    from app import config as config_module

    service = AIService()
    monkeypatch.setattr(config_module.get_settings(), "ollama_base_url", "")
    with pytest.raises(AIServiceError):
        service._get_client()


def test_call_model_maps_auth_error_to_friendly_message(monkeypatch):
    import ollama

    service = AIService()

    class FakeClient:
        def chat(self, *args, **kwargs):
            raise ollama.ResponseError("denied", 403)

    monkeypatch.setattr(service, "_get_client", lambda: FakeClient())

    with pytest.raises(AIServiceError, match="credentials are not configured"):
        service._call_model("prompt")


def test_call_model_maps_model_not_found_to_friendly_message(monkeypatch):
    import ollama

    service = AIService()

    class FakeClient:
        def chat(self, *args, **kwargs):
            raise ollama.ResponseError("model not found", 404)

    monkeypatch.setattr(service, "_get_client", lambda: FakeClient())

    with pytest.raises(AIServiceError, match="model is unavailable"):
        service._call_model("prompt")


def test_call_model_maps_connection_error_to_friendly_message(monkeypatch):
    service = AIService()

    class FakeClient:
        def chat(self, *args, **kwargs):
            raise ConnectionError("refused")

    monkeypatch.setattr(service, "_get_client", lambda: FakeClient())

    with pytest.raises(AIServiceError, match="couldn't connect"):
        service._call_model("prompt")


def test_call_model_returns_message_content_on_success(monkeypatch):
    import ollama

    service = AIService()

    class FakeClient:
        def chat(self, *args, **kwargs):
            return ollama.ChatResponse(message=ollama.Message(role="assistant", content='{"value": 1}'))

    monkeypatch.setattr(service, "_get_client", lambda: FakeClient())

    assert service._call_model("prompt") == '{"value": 1}'
