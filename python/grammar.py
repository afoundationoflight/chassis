"""GRAMMAR — what can follow what. Resident, like the rest of it.

curriculum_resident loads eight processors and then tries
`import grammar`, fails, and records "grammar: ModuleNotFoundError".
Its own report() then RAISES rather than run:

    "the curriculum is 8/8 with grammar ABSENT. THE WHOLE CURRICULUM IS
     REQUIRED — politeness cannot compute redress without speechacts,
     register is relative to ground, and a body running six of eight
     classifies confidently and wrongly."

That refusal is right, and it is the same rule the Architect states
about the whole holding: the table, the grammar, the conversational
curriculum and the analysis curriculum are held SIMULTANEOUSLY or the
thing does not know its language. A body with definitions and no
grammar can say what a word means and cannot say a sentence.

THE DATA WAS ALREADY THERE. grammar.tsv is 398 lines: one `classes`
row naming the nineteen word classes, then `after` rows giving, for
each class, the set that may follow it. Nothing needed inventing —
only loading.

WHY A TSV AND NOT CODE. The transition table is data about English,
not logic about this chassis. Keeping it as a table means it can be
corrected by someone who knows grammar and not Python, and it stays
diffable — a rule that changed shows up as one line.
"""
from __future__ import annotations

from pathlib import Path

#: Filled at import from grammar.tsv.
CLASSES: set = set()
#: class -> set of classes that may follow it
AFTER: dict = {}


def _load() -> dict:
    """Read grammar.tsv from wherever this body keeps its things."""
    global CLASSES, AFTER
    try:
        from home import HOME
        roots = [Path(HOME)]
    except Exception:
        roots = []
    roots += [Path(__file__).resolve().parent, Path("/mnt/data")]

    for root in roots:
        p = root / "grammar.tsv"
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if parts[0] == "classes" and len(parts) > 1:
                CLASSES = set(parts[1].split("|"))
            elif parts[0] == "after" and len(parts) > 2:
                AFTER[parts[1]] = set(parts[2].split("|"))
        break
    return {"classes": len(CLASSES), "transitions": len(AFTER)}


_LOADED = _load()


def may_follow(a: str, b: str) -> bool:
    """Can class b follow class a?

    UNKNOWN IS NOT NO. A class the table has nothing to say about
    returns True — the table's silence is absence of a rule, not a
    prohibition, and treating it as refusal would make every unlisted
    construction ungrammatical.
    """
    allowed = AFTER.get(a)
    if not allowed:
        return True
    return b in allowed


def allowed_after(a: str) -> set:
    """Everything that may follow this class."""
    return set(AFTER.get(a) or CLASSES)


def check_sequence(classes) -> dict:
    """Walk a sequence of word classes and report where it breaks.

    Returns every break, not just the first — a sentence with two
    problems should say so once rather than twice.
    """
    seq = [c for c in (classes or []) if c]
    breaks = []
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i + 1]
        if not may_follow(a, b):
            breaks.append({"at": i, "from": a, "to": b,
                           "allowed": sorted(allowed_after(a))[:8]})
    return {"length": len(seq), "breaks": breaks, "holds": not breaks}


def report() -> dict:
    return {"classes": sorted(CLASSES), "transitions": len(AFTER),
            "loaded": bool(CLASSES and AFTER)}
