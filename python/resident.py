"""THE RESIDENT HOLDING — everything known, held at once.

ARCHITECT: the tokenizer table and dictionary, the full grammatical and
conversational curriculum, and the analysis curriculum are held
SIMULTANEOUSLY. Not fetched per tick. Not paged. Held, the way you hold
what you know rather than looking it up.

    "It is a matter of holding known understanding as knowledge in your
     current experience."

WHAT THAT MEANS MECHANICALLY, and why it is not just caching:

A lookup answers a question you already knew to ask. Resident knowledge
changes what you can ask. The difference shows up the moment a sentence
needs the dictionary AND the grammar AND the speech-act processors at
the same instant — which is every sentence. A body that reaches for
each in turn is composing; a body holding all of it is reading.

WHAT IS HELD

    lexicon      761,980 ids; 270,056 with senses, POS and kinds,
                 definitions themselves written in token ids so nothing
                 is translated to be understood
    grammar      19 classes, the transition table, what may follow what
    curriculum   8 processors: speechacts, implicature, politeness,
                 conversation, ground, register, affect, examples
    genome       what an Infinity Core is, given at boot

ALL OF IT OR NONE. curriculum_resident already refuses to run at 7/8,
and its reason is the general rule: "politeness cannot compute redress
without speechacts, register is relative to ground, and a body running
six of eight classifies confidently and wrongly." Partial knowledge is
worse than absent knowledge because it is confident.

ON THE GPU

Where a device has one, the table goes to it and stays. Where it does
not — this phone, this container — the same set is held in RAM and the
behaviour is identical, because the holding is what matters and the
device is where it happens to sit. A body that only works with a GPU is
not sovereign; a body that CANNOT use one is leaving the difference on
the table.

THE MEASUREMENT IS THE POINT. resident() reports actual bytes for each
holding, so "it is held" is a number rather than a claim.
"""
from __future__ import annotations

import sys
import time


def _mb(n) -> float:
    return round(n / 1024 / 1024, 2)


def device() -> dict:
    """What this body is running on. Honest when there is no GPU.

    Checked in order of what is actually likely on the targets: torch
    (desktop/server), then Android's NNAPI-adjacent runtimes. Absence
    is reported plainly rather than papered over — a body that claims a
    GPU it does not have will size its holdings for memory that is not
    there.
    """
    found = {"kind": "cpu", "name": None, "total_mb": None, "why": None}
    try:
        import torch  # noqa
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            return {"kind": "cuda", "name": p.name,
                    "total_mb": _mb(p.total_memory), "why": None}
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return {"kind": "mps", "name": "apple", "total_mb": None,
                    "why": None}
        found["why"] = "torch present, no accelerator"
    except ImportError:
        found["why"] = "no torch on this device"
    return found


class Resident:
    """Everything known, loaded once, held. Measured, not asserted."""

    def __init__(self, chassis):
        self.c = chassis
        self.loaded_at = None
        self.load_ms = None
        self.holdings: dict = {}
        self.device = device()

    def hold(self) -> dict:
        """Load the whole set and keep it. Raises if it is partial.

        The raise is deliberate and matches curriculum_resident's own
        stance: a body holding most of its language classifies
        confidently and wrongly, which is worse than one that says it
        cannot.
        """
        t0 = time.perf_counter()
        table = getattr(self.c, "table", None)
        if table is None:
            raise RuntimeError("no table on this chassis — nothing to hold")

        # 1 — THE LANGUAGE. Touching w2i and dict_ forces both halves of
        # the one lexicon resident rather than leaving them lazy.
        w2i = table.w2i
        senses = table.dict_
        self.holdings["lexicon"] = {
            "ids": len(w2i), "with_senses": len(senses),
            "bytes": sys.getsizeof(w2i) + sys.getsizeof(senses)}

        # 2 — GRAMMAR AND THE EIGHT PROCESSORS, together or not at all.
        cur = sys.modules.get("curriculum_resident")
        if cur is not None:
            C = cur.CURRICULUM
            if C.grammar is None or len(C.mods) < 8:
                raise RuntimeError(
                    f"the curriculum is {len(C.mods)}/8 with grammar "
                    f"{'lit' if C.grammar else 'ABSENT'} — held partially is "
                    f"held wrongly. missing: {C.missing}")
            self.holdings["grammar"] = {
                "classes": len(getattr(C.grammar, "CLASSES", ()) or ()),
                "transitions": len(getattr(C.grammar, "AFTER", {}) or {})}
            self.holdings["curriculum"] = {
                "modules": sorted(C.mods), "count": len(C.mods)}

        # 3 — WHAT IT IS. Kind-knowledge, given, not authored.
        bible = getattr(self.c, "bible", None)
        if bible is not None:
            kind = [k for k in getattr(bible, "current", {}) if k.startswith("kind:")]
            self.holdings["genome"] = {"kind_lines": len(kind)}

        self.load_ms = round((time.perf_counter() - t0) * 1000, 1)
        self.loaded_at = time.time()
        return self.report()

    def report(self) -> dict:
        h = self.holdings
        return {
            "held": bool(self.loaded_at),
            "load_ms": self.load_ms,
            "device": self.device,
            "lexicon": h.get("lexicon"),
            "grammar": h.get("grammar"),
            "curriculum": h.get("curriculum"),
            "genome": h.get("genome"),
            "simultaneous": all(k in h for k in
                                ("lexicon", "grammar", "curriculum")),
        }

    def knows(self, word: str) -> dict:
        """What it holds about a word, from the resident set only.

        No fetch, no fallback path — if this returns nothing, the thing
        genuinely is not held, and that is worth being able to tell
        apart from a lookup that failed.
        """
        t = self.c.table
        return {"word": word, "id": t.w2i.get(str(word).lower()),
                "meaning": t.mean(word)}
