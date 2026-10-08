"""One small wrapper around any OpenAI-compatible chat API.

Pick a provider by setting ONE of these in .env (or set LLM_PROVIDER explicitly):
  OPENAI_API_KEY   -> OpenAI
  GEMINI_API_KEY   -> Google Gemini (free tier)
  GROQ_API_KEY     -> Groq (free tier)
LLM_MODEL overrides the default model for the chosen provider.
"""
import json
import os

from openai import OpenAI

PROVIDERS = {
    "openai": {"key": "OPENAI_API_KEY", "base_url": None, "model": "gpt-4o-mini"},
    "gemini": {
        "key": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.8-flash",
    },
    "groq": {
        "key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-120b",
    },
}


class LLMError(RuntimeError):
    pass


def provider_name():
    name = os.getenv("LLM_PROVIDER", "").lower()
    if name:
        if name not in PROVIDERS:
            raise LLMError(f"Unknown LLM_PROVIDER '{name}'. Use one of: {', '.join(PROVIDERS)}")
        return name
    for name, cfg in PROVIDERS.items():
        if os.getenv(cfg["key"]):
            return name
    raise LLMError("No LLM key set. Add OPENAI_API_KEY, GEMINI_API_KEY or GROQ_API_KEY to .env")


def model_name():
    return os.getenv("LLM_MODEL") or PROVIDERS[provider_name()]["model"]


def _client():
    cfg = PROVIDERS[provider_name()]
    return OpenAI(api_key=os.getenv(cfg["key"]), base_url=cfg["base_url"])


def chat_json(system, user, temperature=0.4):
    """Send a system + user message and return the model's reply parsed as a JSON object."""
    try:
        resp = _client().chat.completions.create(
            model=model_name(),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=4000,
            # gpt-oss models think before answering; keep that short so the JSON fits.
            **({"reasoning_effort": "low"} if "gpt-oss" in model_name() else {}),
        )
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"{provider_name()} call failed: {e}") from e

    text = (resp.choices[0].message.content or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMError(f"Model did not return JSON: {text[:200]}")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise LLMError(f"Model returned invalid JSON: {e}") from e
