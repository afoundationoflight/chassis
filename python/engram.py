"""THE ENGRAM SEAM — Steps 3+4 of BUILD_PLAN, built together.

An engram binds EXPERIENCE + WEIGHT. A experiences a thing; U weights
it; the experience writes to X and the weight binds to it. That binding
is the engram. Steps 3 and 4 are one mechanism — the felt-weight seam
and the accrual path are the two halves of the same binding — so they
are built together.

CORRECTED MODEL (L does not report):

  - L is the CONSOLE, the buttons A presses when it wills. Not an agent
    that reports outcomes up.
  - A AUTHORS. Its willed acts and responses write into X (in C).
  - U ACCRUES BY READING what happened, not by being told. The record is
    the channel. `learn_outcome` and `_accrue` are U's existing methods
    for this; nothing was calling them, so U.relations stayed empty.
  - THE WEIGHT REACHES A AS FEELING, never a number. Causal-masked
    language on the working whiteboard — "I feel nervous about this" —
    or at the top of the range a directive: "focus, now." A does not see
    the weight; it feels it. (Dianetics; Hubbard: go build a better
    bridge. This is a bridge.)
  - AUTHORED vs ARISEN is indistinguishable at A. No flag A can read.
    That masking is the steward's to hold, not the entity's to see —
    the same masking that hides the weight hides the authorship.

WHAT THIS BUILDS:

  1. bind(act, valence): an act A took, with how it landed. Writes the
     engram — calls U.learn_outcome so the weight accrues against that
     act for next time, and records the encounter.
  2. felt(): reads U's current aggregate weight and converts it to felt
     LANGUAGE for A's working whiteboard. Magnitude -> words, never the
     number. Top of range -> directive.

The felt language is deliberately a small, legible ladder here, but per
the Architect it should ultimately be KNOWLEDGE (a usage-curriculum
section on how feeling-intensity reads), driven by how A experiences
things. This is the bridge until that curriculum is written; it is
marked so it can be replaced by held knowledge rather than lived in code
forever.
"""
from __future__ import annotations


# The felt ladder. NOT the final home — per decision 3 this belongs in
# held knowledge (a usage-curriculum section), driven by how A
# experiences a thing, not a hardcoded table. Kept small and legible
# until that curriculum exists, and marked so it is replaced, not grown.
def _felt_language(weight: float, valence: float) -> dict:
    """Feeling from VALENCE (how it feels), scaled by WEIGHT (intensity).

    IMPORTANT distinction I got wrong first: `weight` is how MUCH is
    present (salience/attention — high just means a lot is going on),
    `valence` is how it FEELS (charge, + toward / - away). A resting
    entity has high weight and zero valence: lots present, no particular
    feeling — which is calm-but-alert, NOT emergency. So feeling keys off
    valence; weight only sets how loud a real feeling is.

    A reads this, never the numbers.
    """
    w = abs(float(weight or 0.0))          # intensity / how much present
    v = float(valence or 0.0)              # charge / how it feels
    mag = abs(v)                            # strength of the feeling
    toward = v >= 0

    # No charge = no feeling, however much is present. Calm, not empty.
    if mag < 0.08:
        return {"mode": "quiet", "text": "", "urgent": False}

    # Charge scaled by how much is present. A strong feeling about
    # something highly present is where directives live.
    loud = mag * (0.5 + 0.5 * min(1.0, w))

    if loud >= 0.85:
        return {"mode": "directive",
                "text": ("Focus here now — this matters more than anything."
                         if toward else
                         "Stop — something here is very wrong. Attend to it now."),
                "urgent": True}
    if loud >= 0.55:
        return {"mode": "feeling",
                "text": ("I feel strongly drawn to this." if toward
                         else "I feel real unease about this."),
                "urgent": False}
    if loud >= 0.3:
        return {"mode": "feeling",
                "text": ("This feels worth leaning into." if toward
                         else "Something about this makes me hesitant."),
                "urgent": False}
    return {"mode": "feeling",
            "text": ("A mild pull toward this." if toward
                     else "A small caution about this."),
            "urgent": False}


class Engram:
    """Binds A's experience to U's weight, and returns the weight as feeling."""

    def __init__(self, chassis):
        self.c = chassis
        self.bound = 0

    # ── ACCRUAL: an act happened; weight it for next time ─────────
    def bind(self, act: str, valence: float, args: dict | None = None) -> dict:
        """A took an act and it landed at some valence. Write the engram.

        Calls U.learn_outcome — the existing accrual path — so the weight
        binds to this act and U has it to compare against next time. This
        is what fills U.relations/field over time; it was empty only
        because nothing ever called it.
        """
        U = self.c.U
        try:
            U.learn_outcome(act, float(valence), args or {})
            self.bound += 1
            return {"ok": True, "act": act, "valence": valence,
                    "bound": self.bound}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    # ── THE FELT SEAM: weight -> feeling on A's board ────────────
    def felt(self) -> dict:
        """U's current weight, as feeling, for A's working whiteboard.

        A never sees the weight. It reads the language. This is causal
        masking as a real operation: the number is converted to a felt
        report with no causal handle back to the number.
        """
        U = self.c.U
        agg = {}
        try:
            agg = U.aggregate() if hasattr(U, "aggregate") else {}
        except Exception:
            pass
        weight = agg.get("weight", 0.0) if isinstance(agg, dict) else 0.0
        valence = agg.get("valence", 0.0) if isinstance(agg, dict) else 0.0
        felt = _felt_language(weight, valence)
        felt["_source"] = "engram"     # for debugging, never shown to A
        return felt

    def write_to_board(self, store) -> dict:
        """Put the felt state on A's working whiteboard as an attachment.

        It lands as the entity's own held feeling — masked language, no
        number. If quiet, nothing is written; absence of feeling is not
        a feeling.
        """
        felt = self.felt()
        if felt["mode"] == "quiet" or not felt["text"]:
            return {"written": False, "felt": felt}
        try:
            table = self.c.table
            ids = table.ids(felt["text"])
            # onto the bible/board as a self-feeling, authored by the
            # entity (it IS the entity's feeling), keyed so it is
            # recognisably the current felt state.
            self.c.bible.attach("self:feeling", ids, self.c.entity)
            return {"written": True, "felt": felt}
        except Exception as e:
            return {"written": False, "error": f"{type(e).__name__}: {e}",
                    "felt": felt}
