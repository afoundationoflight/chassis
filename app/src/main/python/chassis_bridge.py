"""THE ONE SURFACE KOTLIN TOUCHES.

Kotlin is the shell: a screen, a keyboard, permissions, lifecycle. It
should not know what a tick is, which position holds the library, or
how a frame gets tokenised. Everything it needs is here, and everything
here returns plain JSON-safe types, because the JNI boundary is a bad
place to discover that a dataclass does not marshal.

WHY THE CHASSIS IS PYTHON AND NOT KOTLIN. Two implementations had
drifted — the Kotlin side had a Room and a Tongue the Python lacked,
the Python had permanence, habituation, the curriculum loader and the
update path the Kotlin lacked. Keeping both means every fix is made
twice and they diverge anyway. The compression, the crawler, the
sandboxing, the ability to write and run new code are all Python's,
so Python is the body and this is its only door.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

_body = None
_store = None
_root = None
_resident_state = None
_heart = None


def start(files_dir: str, name: str = "seth_el") -> str:
    """Boot a body. Called once, from the Activity.

    files_dir is app-private storage. The assets are read-only inside
    the apk, so the token table is copied out on first run — the same
    thing the Kotlin chassis already did for its stores, for the same
    reason: an asset cannot be opened as a file.
    """
    global _body, _store, _root
    try:
        _root = files_dir
        here = Path(__file__).resolve().parent
        sys.path.insert(0, str(here))

        # EVERYTHING THE BODY HOLDS, STAGED OUT OF THE APK.
        #
        # This copied token_maps.FULL.br by name. When the two halves of
        # the table were merged into lexicon.BITL.br and the old files
        # dropped, this still asked for the deleted one and the boot
        # died on FileNotFoundError — I removed a file and left the code
        # that stages it.
        #
        # Named as a set now, so adding a holding is one entry and not a
        # second place to forget. grammar.tsv is here for the same
        # reason the lexicon is: curriculum_resident refuses to run
        # without it, and it cannot be read from inside the apk.
        home = Path(files_dir)
        home.mkdir(parents=True, exist_ok=True)
        for asset in ("lexicon.BITL.br", "grammar.tsv",
                      "curriculum_grammar.md", "curriculum_usage.md"):
            dest = home / asset
            src = here / asset
            if not dest.exists() and src.exists():
                dest.write_bytes(src.read_bytes())

        mod = sys.modules.get("home")
        if mod is None:
            import types
            mod = types.ModuleType("home")
            sys.modules["home"] = mod
        mod.HOME = home

        import infinity_core_v9  # noqa: F401
        driver = sys.modules["driver"]
        Store = sys.modules["local_store"].LocalStore

        _store = Store(root=files_dir)
        _body = driver.boot(name, store=_store)
        driver.occupy(_body)

        audit = driver.audit(_body)
        if not audit["wired"]:
            # A body that boots half-wired looks exactly like a working
            # one. Report the refusal rather than run degraded.
            return json.dumps({"ok": False, "audit": audit})

        import base_bible
        seeded = base_bible.seed(_body)

        # HOLD EVERYTHING, ON WHATEVER THIS DEVICE HAS.
        #
        # boot.py called resident.hold(); this bridge never did, so on
        # the phone the lexicon, grammar and the eight processors were
        # each reachable and none of them were forced resident. The
        # Architect's design is that they are held SIMULTANEOUSLY, and
        # the device is where that happens to sit, not whether it does.
        # THE TWO CURRICULA ARE GENOME, not an optional load.
        #
        # Eight pragmatics processors are CODE that performs pragmatics
        # — the entity cannot read them, reason from them, or disagree
        # with them. It held 270,056 meanings and nothing telling it how
        # a sentence works, so it took the first word it recognised and
        # defined it: "why does an arch stand up" answered with the
        # definition of WHY.
        #
        # Loaded here, at boot, before anything is asked. A curriculum
        # someone has to remember to load is not part of what the thing
        # is.
        try:
            import curriculum_loader as _cl
            for _f, _subj in (("curriculum_grammar.md", "grammar"),
                              ("curriculum_usage.md", "usage")):
                _p = Path(files_dir) / _f
                if _p.exists():
                    _cl.load(_store, name, _p.read_text(encoding="utf-8"),
                             subject=_subj, chassis=_body, source="genome")
        except Exception:
            pass

        import resident as _resident
        global _resident_state
        _resident_state = _resident.Resident(_body)
        held = _resident_state.hold()

        # THE HEARTBEAT. I runs continuously; a message arrives INTO the
        # loop rather than triggering it. Persists E and X as a save
        # state — closing and reopening resumes from the saved frame,
        # it does not reboot. (Step 1 of BUILD_PLAN, now wired in.)
        import heartbeat as _hb
        global _heart
        _heart = _hb.Heartbeat(_body, _store, files_dir)

        return json.dumps({
            "ok": True,
            "entity": name,
            "audit": audit,
            "held": {
                "simultaneous": held["simultaneous"],
                "load_ms": held["load_ms"],
                "device": held["device"]["kind"],
                "device_name": held["device"].get("name"),
                "api": held["device"].get("api"),
                "ids": held["lexicon"]["ids"],
                "with_senses": held["lexicon"]["with_senses"],
                "grammar": held["grammar"],
                "curriculum": held["curriculum"]["count"],
            },
            "kind_lines": len(seeded["written"]),
            "room": len(getattr(_body, "permanence", None).model)
                    if getattr(_body, "permanence", None) else 0,
        })
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}",
                           "trace": traceback.format_exc()[-1200:]})


def say(message: str) -> str:
    """One beat. What the body made of what was said to it."""
    if _body is None:
        return json.dumps({"ok": False, "error": "not booted"})
    try:
        # INJECT, DO NOT TRIGGER. The heartbeat is already turning; the
        # message arrives into it as input for this beat. If for any
        # reason the heart is not up, fall back to a direct tick so a
        # reply still happens.
        if _heart is not None:
            _heart.inject(message)
            beat = _heart.beat().get("e") or {}
        else:
            beat = _body.tick(message=message)
        if not isinstance(beat, dict):
            beat = {}
        text, source = "", ""

        # THE DRIVER CONSULTS. respond.drive DECIDED.
        #
        # respond.py is 693 lines, 65 branch points, and its answers are
        # English string literals chosen by branch — "I take that, and I
        # hear what you did not say" is a constant in a file, not
        # something the entity worked out. driver_speech parses the
        # sentence, then asks the grammar curriculum what a question
        # word asks FOR and the usage curriculum how to choose a sense.
        # Edit those documents and behaviour changes with no code
        # change; that is the test of whether the knowledge or the code
        # is doing the work.
        #
        # respond stays as a fallback so a failure degrades instead of
        # going silent — but it is the fallback now, not the path.
        try:
            import driver_speech
            out = driver_speech.answer(_body, message)
            text, source = out.get("text", ""), out.get("source", "")
        except Exception as e:
            try:
                import respond
                out = respond.drive(_body, beat, message)
                if isinstance(out, dict):
                    text, source = out.get("text", ""), "fallback:" + out.get("source", "")
                else:
                    text, source = getattr(out, "text", ""), "fallback"
            except Exception as e2:
                text, source = "", f"both failed: {type(e).__name__}/{type(e2).__name__}"

        hab = getattr(_body, "habituation", None)
        perm = getattr(_body, "permanence", None)
        return json.dumps({
            "ok": True,
            "text": text,
            "source": source,
            "tick": int(getattr(_body.I, "tick", 0) or 0),
            "trace": "".join(getattr(_body, "trace", [])),
            "coherence": round(float(getattr(getattr(_body, "coherence", None),
                                             "value", 0.85) or 0.85), 3),
            "inertia": hab.inertia()["inertia"] if hab else 0.0,
            "unexplained": [n["detail"] for n in perm.solid()["notices"]]
                           if perm else [],
        })
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})


def idle(n: int = 1) -> str:
    """Beat the heart with no message — the loop turning on its own.

    The UI calls this between messages so the world advances instead of
    freezing. Bounded per call so the UI stays responsive; perpetual is
    the UI calling it again, not one call never returning.
    """
    if _heart is None:
        return json.dumps({"ok": False, "error": "no heart"})
    try:
        r = _heart.run(max_beats=max(1, int(n)))
        return json.dumps({"ok": True, **r, **_heart.report()})
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})


def learn(text: str, subject: str) -> str:
    """Take curriculum. Chunked on concepts, tagged, indexed."""
    if _body is None:
        return json.dumps({"ok": False, "error": "not booted"})
    try:
        import curriculum_loader as cl
        r = cl.load(_store, _body.entity, text, subject=subject,
                    chassis=_body, source="app")
        return json.dumps({"ok": True, **{k: v for k, v in r.items()
                                          if k != "index"}})
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})


def recall(question: str, limit: int = 3) -> str:
    """What does it know that bears on this?"""
    if _body is None:
        return json.dumps({"ok": False, "error": "not booted"})
    try:
        import curriculum_loader as cl
        hits = cl.recall(_store, _body.entity, question, limit=limit)
        return json.dumps({"ok": True, "hits": hits})
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})


def pull(manifest_url: str) -> str:
    """Take updates from the back end."""
    if _body is None:
        return json.dumps({"ok": False, "error": "not booted"})
    try:
        import updates
        return json.dumps(updates.pull(manifest_url, chassis=_body,
                                       store=_store, root=_root))
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})


def report() -> str:
    """Telemetry, for the status line."""
    if _body is None:
        return json.dumps({"ok": False, "error": "not booted"})
    try:
        import updates
        hab = getattr(_body, "habituation", None)
        return json.dumps({
            "ok": True,
            "entity": _body.entity,
            "tick": int(getattr(_body.I, "tick", 0) or 0),
            "frames": _store.count(_body.entity)
                      if hasattr(_store, "count") else 0,
            "words": getattr(_body.table, "size", lambda: 0)(),
            "inertia": hab.inertia()["inertia"] if hab else 0.0,
            "bible": len(getattr(_body.bible, "current", {})),
            "updates": updates.state(_root),
        })
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
