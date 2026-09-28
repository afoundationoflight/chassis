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

# VERIFIED, not remembered. The previous URL (QuantFactory/TinyStories-33M-GGUF)
# was written from memory and returned HTTP 401 because that repo does not
# exist — there is NO GGUF of TinyStories-33M anywhere; the 33M model ships
# only as PyTorch weights. This points at a real file, checked with a HEAD
# request returning 200 before it went in.
#
# SmolLM2-135M-Instruct at FULL f16 PRECISION (258MB), deliberately NOT
# quantized: a model this small has almost no redundancy to spare, and
# quantization hurts it disproportionately. 258MB costs nothing on-device.
# Instruct-tuned, which suits following the comprehension course better
# than a plain story model would.
GGUF_URL = "https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-f16.gguf"
MODEL_FILE = "smollm2-135m-instruct-f16.gguf"


def _ensure_model(files_dir: str) -> str:
    """Download once, RESUMABLY. A 258MB transfer over real-world wifi
    (a phone screen-locking, a hotel network wobbling) WILL drop
    mid-stream — that is what ConnectionAbortedError was, not a bug in
    the URL or the request. Failing outright and restarting from zero
    every time is unusable at this file size, so this does what a real
    download manager does: keep the partial bytes, ask the server for
    the rest via a Range header, and retry the whole thing a few times
    before giving up.

    The temp-name-then-rename discipline stays — nothing is ever
    mistaken for a complete model until the byte count actually matches
    what the server reported.
    """
    path = os.path.join(files_dir, MODEL_FILE)
    if os.path.exists(path):
        return path

    tmp = path + ".part"
    last_error = None

    for attempt in range(5):
        try:
            existing = os.path.getsize(tmp) if os.path.exists(tmp) else 0
            req = urllib.request.Request(GGUF_URL)
            if existing:
                # RESUME from where the last attempt died, instead of
                # re-pulling bytes already on disk.
                req.add_header("Range", f"bytes={existing}-")

            with urllib.request.urlopen(req, timeout=60) as resp:
                resumed = (resp.status == 206)
                mode = "ab" if (resumed and existing) else "wb"
                if mode == "wb":
                    existing = 0  # server ignored/rejected the Range; start clean
                with open(tmp, mode) as f:
                    while True:
                        chunk = resp.read(1024 * 256)
                        if not chunk:
                            break
                        f.write(chunk)

            # Only a file that reaches a real, complete size gets treated
            # as done. SmolLM2-135M-Instruct-f16.gguf is ~258MB; anything
            # far short of that after a "successful" read is still a
            # dropped connection wearing a clean exit.
            if os.path.getsize(tmp) > 200 * 1024 * 1024:
                os.rename(tmp, path)
                return path
            last_error = RuntimeError(
                f"incomplete after attempt {attempt+1}: "
                f"{os.path.getsize(tmp)} bytes")
        except Exception as e:
            last_error = e
        # Do NOT delete tmp between attempts — that partial progress is
        # exactly what Range resume is for. Only a final, total failure
        # gives up on it.

    if os.path.exists(tmp):
        os.remove(tmp)
    raise RuntimeError(f"model download failed after 5 attempts: "
                       f"{type(last_error).__name__}: {last_error}")


def compose(chassis, message: str, files_dir: str) -> dict:
    """Reach the real JNI-bound model through Chaquopy's Java interop."""
    try:
        from java import jclass
    except ImportError:
        return {"ok": False, "text": "", "error": "not running under Chaquopy"}

    model_path = _ensure_model(files_dir)
    # A Kotlin `object` (singleton) is not a Java static class the way
    # jclass() naively assumes — Kotlin compiles it to a class with an
    # INSTANCE field holding the one real object, and every method call
    # has to go through that instance. Calling LocalTongue.isLoaded()
    # directly on the class reached for an unbound instance method with
    # no instance, which is exactly the TypeError that surfaced: "must
    # be called with ... instance as first argument (got nothing
    # instead)". The model itself loaded fine; only this call shape was
    # wrong.
    LocalTongueClass = jclass("com.omnipolative.chassis.LocalTongue")
    LocalTongue = LocalTongueClass.INSTANCE

    if not LocalTongue.isLoaded():
        ok = LocalTongue.load(model_path)
        if not ok:
            return {"ok": False, "text": "", "error": f"model file missing at {model_path}"}

    system = ("Every sentence has a subject and a predicate. A question word "
             "(what/why/how) tells you what is being asked for. Answer what "
             "was actually asked, briefly.")
    # SmolLM2-Instruct uses the ChatML template. A bare "Question/Answer:"
    # string ignores the format the model was instruct-tuned on, which is
    # most of what makes an instruct model follow a course at all.
    prompt = (f"<|im_start|>system\n{system}<|im_end|>\n"
              f"<|im_start|>user\n{message}<|im_end|>\n"
              f"<|im_start|>assistant\n")

    words = str(LocalTongue.generate(prompt, 60)).strip()
    if not words:
        return {"ok": False, "text": "", "error": "empty generation"}

    import will_speech
    spoken = will_speech.say(chassis, words)
    return {"ok": True, "text": spoken.get("spoke") or words,
           "held_back": spoken.get("held_back", False), "error": None}
