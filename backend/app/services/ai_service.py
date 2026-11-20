"""Centralized AI provider integration.

All calls to the AI provider (Ollama or OpenRouter, chosen by AI_PROVIDER) go through this module. Route handlers
and other services must never call the provider SDK directly - this keeps
authentication, endpoint construction, timeouts, retries and structured-output
parsing in one place. The rest of the application depends only on the
`ai_service` singleton's application-level methods (generate_questions,
interpret_profile, generate_roadmap, classify_checkin, adapt_roadmap) and
never needs to know which provider is behind them.
"""

from __future__ import annotations

import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.core.logging import logger
from app.prompts import (
    SYSTEM_INSTRUCTION,
    build_adapt_prompt,
    build_checkin_prompt,
    build_profile_prompt,
    build_questions_prompt,
    build_roadmap_prompt,
)
from app.schemas.checkin import CheckInClassification
from app.schemas.profile import ProfileFields
from app.schemas.question import QuestionSetResponse
from app.schemas.roadmap import RoadmapPlan

T = TypeVar("T", bound=BaseModel)

REQUEST_TIMEOUT_SECONDS = 60.0
MAX_CORRECTION_RETRIES = 3  # bounded - never infinite, never applied to auth errors


class _Retryable(Exception):
    """A provider failure worth retrying or trying another model for."""

    def __init__(self, status: int) -> None:
        super().__init__(str(status))
        self.status = status


class AIServiceError(Exception):
    """Raised when the AI provider cannot produce a usable structured response.

    Always carries a safe, user-facing message - never the raw provider
    error, a stack trace, or credentials.
    """


class AIService:
    """Thin wrapper around the Ollama client with structured-output validation."""

    def __init__(self) -> None:
        self._client = None
        self._client_signature: tuple[str, str] | None = None

    def _get_client(self):
        settings = get_settings()
        if not settings.has_ai_configured:
            raise AIServiceError("The AI service credentials are not configured correctly.")

        signature = (settings.ollama_base_url, settings.ollama_api_key)
        if self._client is None or self._client_signature != signature:
            import ollama  # imported lazily so the app can start without the dependency installed

            headers = {}
            if settings.ollama_api_key:
                headers["Authorization"] = f"Bearer {settings.ollama_api_key}"
            self._client = ollama.Client(
                host=settings.ollama_base_url,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            self._client_signature = signature
        return self._client

    def _call_openrouter(self, prompt: str, system: str = SYSTEM_INSTRUCTION) -> str:
        """Chat completion via OpenRouter's OpenAI-compatible API (JSON mode)."""

        import httpx

        settings = get_settings()
        if not settings.openrouter_api_key:
            raise AIServiceError("The AI service credentials are not configured correctly.")

        url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-Title": "NextStep AI",
        }

        # Free models are rate-limited unpredictably: try the main model, then
        # each fallback, retrying a rate-limited model once after a short wait.
        models = [settings.openrouter_model] + [
            m.strip() for m in settings.openrouter_fallback_models.split(",") if m.strip()
        ]
        models = list(dict.fromkeys(models))
        last_error: AIServiceError | None = None

        for model in models:
            for attempt in range(2):
                try:
                    return self._openrouter_once(url, headers, model, prompt, system)
                except _Retryable as exc:
                    last_error = AIServiceError(_status_message(exc.status))
                    if exc.status == 429 and attempt == 0:
                        time.sleep(2)
                        continue
                    break  # next model
        raise last_error or AIServiceError("The AI service is temporarily unavailable.")

    def _openrouter_once(self, url: str, headers: dict, model: str, prompt: str, system: str = SYSTEM_INSTRUCTION) -> str:
        import httpx

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
        }
        logger.info("AI request started (provider=openrouter, model=%s)", model)
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        except httpx.TimeoutException as exc:
            logger.error("AI request failed: TimeoutException")
            raise AIServiceError("The AI service took too long to respond. Please try again.") from exc
        except httpx.HTTPError as exc:
            logger.error("AI request failed: %s", type(exc).__name__)
            raise AIServiceError(
                "We couldn't connect to the AI service. Please check the AI configuration and try again."
            ) from exc

        status = response.status_code
        if status >= 400:
            logger.error("AI request failed: OpenRouter status=%s model=%s", status, model)
            if status in (404, 429, 500, 502, 503, 504):
                raise _Retryable(status)
            raise AIServiceError(_status_message(status))

        try:
            body = response.json()
        except ValueError as exc:
            raise AIServiceError("The AI service returned an unreadable response.") from exc

        # OpenRouter can report upstream errors inside a 200 response.
        if isinstance(body, dict) and body.get("error"):
            code = body["error"].get("code") if isinstance(body["error"], dict) else None
            logger.error("AI request failed: OpenRouter error code=%s model=%s", code, model)
            raise _Retryable(code if isinstance(code, int) else 503)

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("AI request failed: unexpected OpenRouter response shape")
            raise _Retryable(503) from exc

        if not (content or "").strip():
            # Free models sometimes return an empty message; try another model.
            logger.error("AI request failed: empty response model=%s", model)
            raise _Retryable(503)

        logger.info("AI request completed")
        return content

    def _call_model(self, prompt: str, system: str = SYSTEM_INSTRUCTION) -> str:
        settings = get_settings()
        if settings.ai_provider.strip().lower() == "openrouter":
            return self._call_openrouter(prompt, system)

        import ollama

        client = self._get_client()
        logger.info("AI request started (model=%s)", settings.ollama_model)
        try:
            response = client.chat(
                model=settings.ollama_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                format="json",
                options={"temperature": 0.2, "num_predict": 4096},
            )
        except ollama.ResponseError as exc:
            logger.error("AI request failed: ResponseError status=%s", exc.status_code)
            if exc.status_code in (401, 403):
                raise AIServiceError("The AI service credentials are not configured correctly.") from exc
            if exc.status_code == 402:
                raise AIServiceError(
                    "The AI service's usage limit has been reached. Please try again later."
                ) from exc
            if exc.status_code == 404:
                raise AIServiceError(
                    "The configured AI model is unavailable. Please check the model configuration."
                ) from exc
            if exc.status_code == 429:
                raise AIServiceError(
                    "The AI service is receiving too many requests right now. Please try again shortly."
                ) from exc
            raise AIServiceError("The AI service is temporarily unavailable.") from exc
        except ConnectionError as exc:
            logger.error("AI request failed: ConnectionError")
            raise AIServiceError(
                "We couldn't connect to the AI service. Please check the AI configuration and try again."
            ) from exc
        except TimeoutError as exc:
            logger.error("AI request failed: TimeoutError")
            raise AIServiceError("The AI service took too long to respond. Please try again.") from exc
        except Exception as exc:  # unexpected network/library errors
            logger.error("AI request failed: %s", type(exc).__name__)
            raise AIServiceError("The AI service is temporarily unavailable.") from exc

        logger.info("AI request completed")
        return response.message.content or ""

    def generate_structured(self, prompt: str, schema_model: type[T]) -> T:
        """Call the AI provider and validate the JSON response against schema_model.

        Retries with a correction instruction (up to MAX_CORRECTION_RETRIES
        times) if a response is not valid JSON matching the schema. Raises
        AIServiceError if every attempt fails, so callers can preserve
        existing data and show a safe error instead of crashing or saving
        invalid AI output. This is a bounded retry (never infinite, and never
        applied to authentication errors - those raise immediately from
        `_call_model` before reaching this loop).
        """

        current_prompt = prompt
        last_error: Exception | None = None
        for attempt in range(MAX_CORRECTION_RETRIES + 1):
            raw = self._call_model(current_prompt)
            try:
                return schema_model.model_validate_json(_extract_json(raw))
            except (ValidationError, ValueError) as error:
                last_error = error
                if attempt < MAX_CORRECTION_RETRIES:
                    logger.warning("AI response failed validation (attempt %d), retrying", attempt + 1)
                    current_prompt = (
                        f"{prompt}\n\nYour previous response was invalid: {error}. "
                        f"Respond again with ONLY a single valid JSON object matching the schema. "
                        f"Check every bracket and comma carefully."
                    )

        logger.error("AI response failed validation after %d attempts: %s", MAX_CORRECTION_RETRIES + 1, last_error)
        raise AIServiceError("The AI returned an unusable response.") from last_error

    # -- Specialized responsibilities -------------------------------------------------

    def generate_questions(
        self,
        goal_title: str,
        goal_description: str,
        known_profile: dict,
        previous_answers: list[dict],
        questions_remaining: int,
        target_date: str = "",
    ) -> QuestionSetResponse:
        prompt = build_questions_prompt(
            goal_title, goal_description, known_profile, previous_answers, questions_remaining, target_date
        )
        return self.generate_structured(prompt, QuestionSetResponse)

    def interpret_profile(
        self, goal_title: str, goal_description: str, answers: list[dict], target_date: str = ""
    ) -> ProfileFields:
        prompt = build_profile_prompt(goal_title, goal_description, answers, target_date)
        return self.generate_structured(prompt, ProfileFields)

    def generate_roadmap(
        self, goal_title: str, goal_description: str, profile: dict, target_date: str = ""
    ) -> RoadmapPlan:
        prompt = build_roadmap_prompt(goal_title, goal_description, profile, target_date)
        return self.generate_structured(prompt, RoadmapPlan)

    def classify_checkin(self, message: str, current_task_titles: list[str]) -> CheckInClassification:
        prompt = build_checkin_prompt(message, current_task_titles)
        return self.generate_structured(prompt, CheckInClassification)

    def adapt_roadmap(
        self,
        goal_title: str,
        profile: dict,
        classification: dict,
        remaining_roadmap: dict,
        target_date: str = "",
        completed_task_titles: list[str] | None = None,
    ) -> RoadmapPlan:
        prompt = build_adapt_prompt(
            goal_title, profile, classification, remaining_roadmap, target_date, completed_task_titles
        )
        return self.generate_structured(prompt, RoadmapPlan)


def _status_message(status: int) -> str:
    """Safe, user-facing message for a provider HTTP status."""

    if status in (401, 403):
        return "The AI service credentials are not configured correctly."
    if status == 402:
        return "The AI service's usage limit has been reached. Please try again later."
    if status == 404:
        return "The configured AI model is unavailable. Please check the model configuration."
    if status == 429:
        return "The AI service is receiving too many requests right now. Please try again shortly."
    return "The AI service is temporarily unavailable."


def _extract_json(raw: str) -> str:
    """Strip markdown code fences if the model wraps JSON despite instructions."""

    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    # Some models add prose or reasoning around the object; keep the outermost braces.
    if not text.startswith("{") and "{" in text and "}" in text:
        text = text[text.index("{") : text.rindex("}") + 1]
    return text.strip()


ai_service = AIService()
