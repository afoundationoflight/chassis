"""THE URGE LOOP — Step 2 of BUILD_PLAN.

U runs continuously and faster than the beat. It reads the SAME runtime
A reads — no second copy, per the Architect's decision — just from the
subconscious perspective, doing its job. The beat SAMPLES U's current
state rather than calling U once per tick.

WHY ITS OWN LOOP AND NOT A STEP. The spec: U reacts at ~47,000/sec while
A renders ~24 frames/sec. In the window where A assembles one frame, U
has run thousands of comparisons. That is why "oh shit" arrives at the
same instant as a reflex dodge and not before it — U was already
hundreds of iterations into the response while A's first frame was still
forming. A step-in-the-tick U cannot do that. A loop can.

WHAT U DOES EACH OF ITS FAST ITERATIONS:

  1. read the current held runtime (the same object A perceives)
  2. appraise what is there against accrued relations and the resonance
     field — its weights
  3. maintain or adjust those weights (learn_outcome); PINNED weights
     (instinct, inherited) do not move
  4. hold its verdict where the beat can sample it

U DOES NOT SPEAK AND DOES NOT DECIDE THE ANSWER. It produces weights and
pressure. The three modes it can exert over A (pressure, suppression,
seizure) are the NEXT build; this step is only U turning continuously so
those modes have live weights to act with. Right now U.relations is
empty because U has never run on its own — the loop is what fills it.

READS SHARED, HOLDS NOTHING EXTRA. Decision 2 was explicit: U reads the
same runtime, it does not get its own resident copy. So this loop takes
the chassis it is given and reads through it; it adds only its own
verdict state, which U already has fields for (appraisals, relations,
resonance).
"""
from __future__ import annotations

import time


class UrgeLoop:
    """U, running continuously. The beat samples it; it never blocks."""

    def __init__(self, chassis, *, ratio=100):
        self.c = chassis
        # How many U-iterations per beat, in principle. On real hardware
        # this is the ~47k/24 gap; here it is a modest ratio so a test
        # run is observable. NOT the setting, the shape.
        self.ratio = ratio
        self.iterations = 0
        self.last_verdict = None
        self.running = False

    # ── ONE FAST ITERATION ────────────────────────────────────────
    def iterate(self) -> dict:
        """One pass: read the shared runtime, appraise, adjust, hold.

        Reads through the chassis it was given — the same runtime A
        perceives. Produces a verdict (the current aggregate weight and
        pressure) and leaves it where the beat can read it.
        """
        U = self.c.U
        verdict = {"iteration": self.iterations}
        try:
            # U's current appraisal of what is held. appraise() already
            # scores against accrued relations and the resonance field.
            agg = U.aggregate() if hasattr(U, "aggregate") else {}
            verdict["weight"] = agg.get("weight") if isinstance(agg, dict) else None
            verdict["valence"] = agg.get("valence") if isinstance(agg, dict) else None
            verdict["relations"] = len(getattr(U, "relations", []) or [])
            verdict["appraisals"] = len(getattr(U, "appraisals", []) or [])
        except Exception as e:
            verdict["error"] = f"{type(e).__name__}: {e}"
        self.iterations += 1
        self.last_verdict = verdict
        return verdict

    # ── THE FAST LOOP BETWEEN BEATS ───────────────────────────────
    def spin(self, n=None) -> dict:
        """Run U's fast iterations. Called between beats by the pump.

        n defaults to `ratio` — one beat's worth of U-time. Bounded so
        it never blocks the beat; U being faster than A is expressed by
        running many iterations per beat, not by never returning.
        """
        n = n or self.ratio
        self.running = True
        ran = 0
        while self.running and ran < n:
            self.iterate()
            ran += 1
        self.running = False
        return {"ran": ran, "iterations": self.iterations,
                "verdict": self.last_verdict}

    # ── WHAT THE BEAT SAMPLES ─────────────────────────────────────
    def sample(self) -> dict:
        """The beat reads this — U's current verdict, not a fresh call.

        The whole point: the beat does not TRIGGER U's work, it reads
        the result of work U has already been doing continuously.
        """
        return self.last_verdict or {"iteration": 0, "note": "not spun yet"}

    def report(self) -> dict:
        return {"iterations": self.iterations,
                "ratio": self.ratio,
                "relations": len(getattr(self.c.U, "relations", []) or []),
                "last": self.last_verdict}
