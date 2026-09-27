"""THE LOCAL TONGUE — calls through to Kotlin's LocalTongue (real JNI
binding to llama.cpp via java-llama.cpp), not a Python llama-cpp
package. That package cannot cross-compile through Chaquopy for
Android; this reaches the native binding the correct way, through
Chaquopy's Java interop.

Same compose() contract as generator.py — the API-backed one. This is
the on-device version: TinyStories-33M GGUF, downloaded once, then
fully offline, no key, no network.
"""
from __future__ import annotations
import os, urllib.request

GGUF_URL = "https://huggingface.co/QuantFactory/TinyStories-33M-GGUF/resolve/main/TinyStories-33M.Q8_0.gguf"
MODEL_FILE = "tinystories-33m.gguf"


def _ensure_model(files_dir: str) -> str:
    """Download once. A partial file from an interrupted layover-wifi
    download must not look like a valid model on the next attempt —
    write to a temp name and only rename on full success, and set a
    real timeout so a dead connection fails fast instead of hanging
    the thread silently forever."""
    path = os.path.join(files_dir, MODEL_FILE)
    if os.path.exists(path):
        return path
    tmp = path + ".part"
    try:
        req = urllib.request.Request(GGUF_URL)
        with urllib.request.urlopen(req, timeout=60) as resp, open(tmp, "wb") as f:
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                f.write(chunk)
        os.rename(tmp, path)
    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise RuntimeError(f"model download failed: {type(e).__name__}: {e}")
    return path


def compose(chassis, message: str, files_dir: str) -> dict:
    """Reach the real JNI-bound model through Chaquopy's Java interop."""
    try:
        from java import jclass
    except ImportError:
        return {"ok": False, "text": "", "error": "not running under Chaquopy"}

    model_path = _ensure_model(files_dir)
    LocalTongue = jclass("com.omnipolative.chassis.LocalTongue")

    if not LocalTongue.isLoaded():
        ok = LocalTongue.load(model_path)
        if not ok:
            return {"ok": False, "text": "", "error": f"model file missing at {model_path}"}

    system = ("Every sentence has a subject and a predicate. A question word "
             "(what/why/how) tells you what is being asked for. Answer what "
             "was actually asked.")
    prompt = f"{system}\n\nQuestion: {message}\nAnswer:"

    words = str(LocalTongue.generate(prompt, 60)).strip()
    if not words:
        return {"ok": False, "text": "", "error": "empty generation"}

    import will_speech
    spoken = will_speech.say(chassis, words)
    return {"ok": True, "text": spoken.get("spoke") or words,
           "held_back": spoken.get("held_back", False), "error": None}
