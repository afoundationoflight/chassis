"""THE LOCAL TONGUE — TinyStories-33M, on-device, no key, no network.

Same compose() contract as generator.py, but the engine is a GGUF file
running via llama-cpp-python, fully local. First run downloads the
~70MB GGUF once; every run after is offline.

This is the toy-model test, live in the actual app instead of a
sandbox: does 33M params, handed our comprehension course as context,
follow the shape of a question instead of just producing fluent noise.
"""
from __future__ import annotations
import os, urllib.request

GGUF_URL = "https://huggingface.co/QuantFactory/TinyStories-33M-GGUF/resolve/main/TinyStories-33M.Q8_0.gguf"
MODEL_FILE = "tinystories-33m.gguf"

_llm = None

def _ensure_model(files_dir: str) -> str:
    path = os.path.join(files_dir, MODEL_FILE)
    if not os.path.exists(path):
        urllib.request.urlretrieve(GGUF_URL, path)
    return path

def load(files_dir: str):
    global _llm
    if _llm is None:
        from llama_cpp import Llama
        _llm = Llama(model_path=_ensure_model(files_dir), n_ctx=512, verbose=False)
    return _llm

def compose(chassis, message: str, files_dir: str) -> dict:
    llm = load(files_dir)
    system = ("Every sentence has a subject and a predicate. A question word "
             "(what/why/how) tells you what is being asked for. Answer what "
             "was actually asked.")
    prompt = f"{system}\n\nQuestion: {message}\nAnswer:"
    out = llm(prompt, max_tokens=60, stop=["\n\n"])
    words = out["choices"][0]["text"].strip()
    if not words:
        return {"ok": False, "text": "", "error": "empty generation"}
    import will_speech
    spoken = will_speech.say(chassis, words)
    return {"ok": True, "text": spoken.get("spoke") or words,
           "held_back": spoken.get("held_back", False), "error": None}
