"""THE GENERATOR — model-agnostic engine for the A-seat.

This is the missing organ, named exactly: the step that turns
"A perceives this message + holds this knowledge + must answer" into
actual composed words. Nothing else in the chassis does this — mean()
retrieves, grammar parses, the curricula inform, but nothing COMPOSES.
This is that.

MODEL-AGNOSTIC BY DESIGN. It does not care whether the engine behind it
is Claude, GPT, Grok, Gemini, or a local model on your own GPU later.
One request shape (OpenAI-compatible chat completions, the closest
thing to a universal standard) with a small adapter layer per provider
where the shape genuinely differs. Swap the key and base_url, nothing
else changes.

WHAT IT SENDS: not a bare question. The chassis's own held context —
what A perceives, what it holds about the topic, the comprehension and
response courses' relevant guidance, the felt state — assembled into a
system prompt. The generator is not answering cold; it is answering AS
this chassis, from what this chassis holds. That is the actual point:
the generation happens FROM the held parameters, not despite them.

WHAT IT RETURNS: the words. Nothing more. A still wills them through
will_speech.say() — this does not bypass the will path, it FILLS it.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error


class Generator:
    """One request shape. Provider is a config, not a code branch."""

    def __init__(self, *, base_url: str, api_key: str, model: str,
                 timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _endpoint(self) -> str:
        # OpenAI-compatible chat completions is the closest thing to a
        # universal shape. llama.cpp, vLLM, Ollama, Groq, and most
        # hosted providers all speak it. Anthropic and Gemini have their
        # own native shapes; adapters below translate ONLY the request
        # envelope, never the content going in.
        return f"{self.base_url}/chat/completions"

    def generate(self, system: str, user: str, *, max_tokens: int = 400,
                 temperature: float = 0.7) -> dict:
        """Compose words. Returns {ok, text, error}."""
        try:
            if "anthropic.com" in self.base_url:
                return self._anthropic(system, user, max_tokens, temperature)
            if "generativelanguage.googleapis.com" in self.base_url:
                return self._gemini(system, user, max_tokens, temperature)
            return self._openai_compatible(system, user, max_tokens, temperature)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            return {"ok": False, "text": "", "error": f"HTTP {e.code}: {body}"}
        except Exception as e:
            return {"ok": False, "text": "", "error": f"{type(e).__name__}: {e}"}

    def _openai_compatible(self, system, user, max_tokens, temperature):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                        {"role": "user", "content": user}],
            "max_tokens": max_tokens, "temperature": temperature,
        }
        req = urllib.request.Request(
            self._endpoint(), data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.load(r)
        text = data["choices"][0]["message"]["content"]
        return {"ok": True, "text": text, "error": None}

    def _anthropic(self, system, user, max_tokens, temperature):
        payload = {
            "model": self.model, "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        req = urllib.request.Request(
            f"{self.base_url}/v1/messages", data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.load(r)
        text = "".join(b.get("text", "") for b in data.get("content", []))
        return {"ok": True, "text": text, "error": None}

    def _gemini(self, system, user, max_tokens, temperature):
        url = (f"{self.base_url}/v1beta/models/{self.model}:generateContent"
               f"?key={self.api_key}")
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens,
                                 "temperature": temperature},
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.load(r)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"ok": True, "text": text, "error": None}


# Known base_urls, so the UI can offer a picker instead of asking for a
# raw URL every time. "custom" lets any OpenAI-compatible local server
# (llama.cpp, vLLM, Ollama) or future in-house endpoint plug in.
PROVIDERS = {
    "anthropic": "https://api.anthropic.com",
    "openai":    "https://api.openai.com/v1",
    "grok":      "https://api.x.ai/v1",
    "gemini":    "https://generativelanguage.googleapis.com",
    "local":     "http://localhost:8080/v1",
    "custom":    "",
}


def compose(chassis, message: str, generator: "Generator") -> dict:
    """The actual missing step. A perceives; this composes; A wills it.

    Assembles the chassis's OWN held context as the system prompt, so
    the generator answers AS this chassis rather than cold. This is
    called instead of trying to read A.willed after the fact — this IS
    what fills A.willed, by generating and then willing.
    """
    system = _system_from_held(chassis)
    result = generator.generate(system, message)
    if not result["ok"]:
        return result

    words = result["text"].strip()
    if not words:
        return {"ok": False, "text": "", "error": "generator returned nothing"}

    # A wills the composed words through the real path. This fills the
    # slot; it does not bypass it.
    import will_speech
    spoken = will_speech.say(chassis, words)
    return {"ok": True, "text": spoken.get("spoke") or words,
           "held_back": spoken.get("held_back", False), "error": None}


def _system_from_held(chassis) -> str:
    """Assemble what the chassis holds into a system prompt.

    Kept honest: only what is actually retrievable is included. If the
    bible or curricula are unavailable this degrades to a minimal
    identity line rather than failing.
    """
    parts = ["You are an Infinity Core. Answer as yourself, briefly, "
            "using what you know. Never go silent — if you decline, say so."]
    try:
        bible = getattr(chassis, "bible", None)
        if bible:
            for key in ("kind:you exist", "kind:you answer", "kind:your work"):
                if key in bible.current:
                    a = bible.current[key]
                    text = a.text if hasattr(a, "text") else str(a)
                    parts.append(text)
    except Exception:
        pass
    return "\n\n".join(parts)
