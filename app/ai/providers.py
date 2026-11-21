"""Bring-your-own-key AI providers behind one interface: generate_json(...) -> dict.

Each student supplies their own API key, so usage is billed to and rate-limited on their key,
never on a key owned by the app. SDKs are imported lazily so the app runs without them.
"""
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderInfo:
    key: str
    label: str
    default_model: str
    key_hint: str
    key_url: str


PROVIDERS = {
    "claude": ProviderInfo("claude", "Anthropic Claude", "claude-opus-5-5", "sk-ant-...",
                           "https://platform.claude.com/settings/keys"),
    "openai": ProviderInfo("openai", "OpenAI", "gpt-4.1-mini", "sk-...",
                           "https://platform.openai.com/api-keys"),
    "gemini": ProviderInfo("gemini", "Google Gemini", "gemini-2.5-flash", "AIza...",
                           "https://aistudio.google.com/apikey"),
}

TIMEOUT_SECONDS = 120
# Claude models that accept server-side refusal fallbacks (re-run on another model if declined).
_CLAUDE_FALLBACK_MODELS = {"claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-opus-5",
                           "claude-sonnet-5-5"}

MESSAGES = {
    "invalid_key": "The AI provider rejected your API key. Check it in Settings.",
    "quota": "Your API key has no remaining credit or quota. Check your provider's billing page.",
    "rate_limited": "Your API key hit the provider's rate limit. Wait a minute and try again.",
    "model_not_found": "The selected model isn't available for your key. Choose another model in Settings.",
    "refused": "The AI declined this request. Try different wording or use default mode.",
    "unavailable": "The AI provider couldn't be reached. Try again later or use default mode.",
    "bad_response": "The AI returned an unexpected response. Try again or use default mode.",
    "bad_request": "The AI provider rejected the request.",
}


class ProviderError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(MESSAGES.get(code, MESSAGES["bad_response"]))


def generate_json(provider: str, api_key: str, model: str, system: str, prompt: str,
                  schema: dict, max_tokens: int = 16000) -> dict:
    """Ask the provider for a JSON object matching ``schema``. Raises ProviderError."""
    adapters = {"claude": _claude, "openai": _openai, "gemini": _gemini}
    if provider not in adapters:
        raise ProviderError("bad_request", f"Unknown provider '{provider}'")
    try:
        text = adapters[provider](api_key, model, system, prompt, schema, max_tokens)
    except ImportError as exc:
        raise ProviderError("unavailable", f"SDK not installed: {exc}") from exc
    try:
        data = json.loads(text)
    except (TypeError, ValueError) as exc:
        raise ProviderError("bad_response", "Response was not valid JSON") from exc
    if not isinstance(data, dict):
        raise ProviderError("bad_response", "Response JSON was not an object")
    return data


def test_connection(provider: str, api_key: str, model: str) -> None:
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}},
              "required": ["ok"], "additionalProperties": False}
    generate_json(provider, api_key, model, "Reply with JSON only.", 'Return {"ok": true}.', schema,
                  max_tokens=2048)


# ------------------------------------------------------------------- Anthropic
def _claude(api_key, model, system, prompt, schema, max_tokens) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=1)
    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
    )
    try:
        if model in _CLAUDE_FALLBACK_MODELS:
            response = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
        else:
            response = client.messages.create(**kwargs)
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
        raise ProviderError("invalid_key", exc.message) from exc
    except anthropic.NotFoundError as exc:
        raise ProviderError("model_not_found", exc.message) from exc
    except anthropic.RateLimitError as exc:
        raise ProviderError("rate_limited", exc.message) from exc
    except anthropic.BadRequestError as exc:
        code = "quota" if "credit" in exc.message.lower() else "bad_request"
        raise ProviderError(code, exc.message) from exc
    except anthropic.APIStatusError as exc:
        raise ProviderError("unavailable" if exc.status_code >= 500 else "bad_request", exc.message) from exc
    except anthropic.APIConnectionError as exc:  # includes timeouts
        raise ProviderError("unavailable", str(exc)) from exc

    if response.stop_reason == "refusal":
        raise ProviderError("refused")
    if response.stop_reason == "max_tokens":
        raise ProviderError("bad_response", "Response was cut off (max_tokens)")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ProviderError("bad_response", "No text in response")
    return text


# ---------------------------------------------------------------------- OpenAI
def _openai(api_key, model, system, prompt, schema, max_tokens) -> str:
    import openai

    client = openai.OpenAI(api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=1)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            response_format={"type": "json_schema",
                             "json_schema": {"name": "result", "schema": schema, "strict": True}},
        )
    except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
        raise ProviderError("invalid_key", str(exc)) from exc
    except openai.NotFoundError as exc:
        raise ProviderError("model_not_found", str(exc)) from exc
    except openai.RateLimitError as exc:
        code = "quota" if getattr(exc, "code", None) == "insufficient_quota" else "rate_limited"
        raise ProviderError(code, str(exc)) from exc
    except openai.BadRequestError as exc:
        raise ProviderError("bad_request", str(exc)) from exc
    except openai.APIStatusError as exc:
        raise ProviderError("unavailable" if exc.status_code >= 500 else "bad_request", str(exc)) from exc
    except openai.APIConnectionError as exc:
        raise ProviderError("unavailable", str(exc)) from exc

    message = response.choices[0].message
    if getattr(message, "refusal", None):
        raise ProviderError("refused")
    if response.choices[0].finish_reason == "length":
        raise ProviderError("bad_response", "Response was cut off")
    return message.content


# ---------------------------------------------------------------------- Gemini
def _gemini(api_key, model, system, prompt, schema, max_tokens) -> str:
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_json_schema=schema,
            ),
        )
    except errors.ClientError as exc:
        text = f"{exc.status or ''} {exc.message or ''}".lower()
        if exc.code in (401, 403) or "api key" in text:
            code = "invalid_key"
        elif exc.code == 404:
            code = "model_not_found"
        elif exc.code == 429:
            code = "quota" if "quota" in text else "rate_limited"
        else:
            code = "bad_request"
        raise ProviderError(code, str(exc)) from exc
    except errors.APIError as exc:  # ServerError and others
        raise ProviderError("unavailable", str(exc)) from exc
    except OSError as exc:  # network failures
        raise ProviderError("unavailable", str(exc)) from exc

    text = response.text
    if not text:
        raise ProviderError("refused" if getattr(response, "prompt_feedback", None) else "bad_response")
    return text
