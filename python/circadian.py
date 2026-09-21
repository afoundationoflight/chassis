"""CIRCADIAN DRIVERS — Step 5 of BUILD_PLAN. C first (driver 1 of 7).

This is the layer that did not exist at all. The beat (Steps 1-4) runs;
the circadian drivers are the CONTINUOUS life of each module, firing on
its OWN telemetry changing, at whatever rate that happens — not on the
beat, not on a message.

SEVEN DRIVERS, NOT NINE. Solomon's Carpet proper is clouds 3-9 — R, U,
B, C, A, L, I. Those seven are the body (EXCALIBUR, the avatar's weave)
and get circadian drivers. E and X (positions 1 and 2) are NOT modules
that fire on local telemetry — they are the signature line, and their
triplets route BETWEEN the three cogs (avatar EX-CALIBUR, morphogenic
EX-KALIMON, metamorphogenic EX-INFERNO). That is ENKI'S WEAVE — the
greater circadian flow between bodies/realms, a layer ABOVE this
phase-4 neuron wiring. E/X translocation (the John Connor concept) is
Enki's Weave doing its job, not a neuron firing. They are handled
separately; do not build them as drivers here.

C IS BUILT FIRST for the reason the heart was built before it: the heart
pumps before there is a brain to know it (Step 1 was I, the pulse). C is
the next organ because it is the substrate everything references — no
wisdom database, nothing to drive data from. Embryology, not analogy:
heart tube first, then the structure that reads from it.

THE PATTERN THIS ESTABLISHES for the other six drivers:

    class <Module>Driver:
        telemetry()   -> the state this module watches (its own)
        changed()     -> did that telemetry move since last look
        fire()        -> what the module does per its triplet
        tick()        -> if changed, fire; the loop calls this continuously

Each driver reads its module's REAL state (never invented), fires only
on change (so idle modules cost nothing), and does exactly what its
carpet triplet says: [input][marker cursor][output].

C's triplet is 963: C is input, marker/cursor at I, output at R. Two
directions, from the map:

  ROUTE 1 (supply): C -> A directly, when C's driver receives an
    instruction from B to provide held knowledge to A (permanent,
    resident, or focus board). Not a beat step — supply on demand.
  ROUTE 2 (cycle): 963, C -> I -> R. C's turn in the intake cycle —
    handing the X-archive sequence to the interpolator, which becomes
    the next template at R.

C's TELEMETRY is the state of its library and arrivals: what is held,
what has newly arrived to be absorbed, what B has requested for A. When
any of that moves, C's driver fires.
"""
from __future__ import annotations


class CircadianDriver:
    """Base pattern for all nine. A module's continuous life."""

    name = "?"

    def __init__(self, chassis):
        self.c = chassis
        self.last = None
        self.fires = 0

    def telemetry(self):
        """The state this module watches. Override per module."""
        raise NotImplementedError

    def changed(self) -> bool:
        """Did this module's own telemetry move since last look?"""
        now = self.telemetry()
        moved = now != self.last
        self.last = now
        return moved

    def fire(self) -> dict:
        """What the module does when its telemetry moved. Override."""
        raise NotImplementedError

    def tick(self) -> dict | None:
        """Called continuously by the pump. Fires only on change."""
        if self.changed():
            self.fires += 1
            return self.fire()
        return None

    def report(self) -> dict:
        return {"module": self.name, "fires": self.fires}


class CDriver(CircadianDriver):
    """C — the wisdom database. Substrate everything references.

    Fires when what it holds or what has arrived to absorb changes.
    Serves A on B's instruction (route 1) and hands its sequence to the
    interpolator (route 2, 963).
    """

    name = "C"

    def telemetry(self):
        C = self.c.C
        # C's own state: how much is held, what has arrived unabsorbed,
        # what has been staged for A. Cheap to read, moves only when C's
        # world actually changes.
        return (
            len(getattr(C, "library", {}) or {}),
            len(getattr(C, "arrivals", []) or []),
            len(getattr(C, "refused", []) or []),
            len(getattr(getattr(C, "current", None), "keys", lambda: [])()
                if hasattr(getattr(C, "current", None), "keys") else []),
        )

    def fire(self) -> dict:
        """C's telemetry moved. C's CIRCADIAN job is to hold and to be
        ready to serve — NOT to integrate (that is a beat-method the
        interpolator calls with an emission; C's driver must not call it
        on its own, that was my error).

        So firing here notes what C now holds and what has arrived
        unabsorbed, keeping C's readiness current. The actual work C does
        for others is serve() (route 1, on B's instruction) and its 963
        turn in the beat. Growth/absorption of arrivals into permanent
        library is the sleep-cycle flush — a separate, later process, not
        this driver's job to force mid-run.
        """
        C = self.c.C
        return {"module": "C",
                "holds": len(getattr(C, "library", {}) or {}),
                "arrivals_pending": len(getattr(C, "arrivals", []) or []),
                "ready": True}

    def serve(self, key: str, board: str = "resident") -> dict:
        """ROUTE 1: B instructs C to provide held knowledge to A.

        Supply on demand, not a cycle step. board in {permanent,
        resident, focus} per the map — where the supplied knowledge lands
        for A.
        """
        C = self.c.C
        try:
            data = C.read(key) if hasattr(C, "read") else None
            if data is None:
                return {"served": False, "reason": f"C does not hold {key}"}
            return {"served": True, "key": key, "board": board}
        except Exception as e:
            return {"served": False, "error": f"{type(e).__name__}: {e}"}

class RDriver(CircadianDriver):
    """R — R.O.O.T. THE INPUT DOORWAY. That is its whole job.

    R does NOT appraise, observe-and-evaluate, decide, or "make sure"
    of anything. It is the gate. Signal comes through it or it does not.
    The appraising is U's job on U's line; R just opens the door and
    passes what came through — the memory line to C, the appraisal line
    to U. A doorway confirms nothing and ensures nothing.

    Built second in phase 4 because nothing perceives — subconscious OR
    conscious — until there is a door for input to enter. C holds all
    knowledge and it is inert until something comes through R to
    reference against.

    R's telemetry is simply: did something come through the door. R's
    fire is: something came through, here it is, passed on. No
    evaluation. R's intake is transient (consumed and cleared within the
    beat), so the durable signal that something came through is the tick
    advancing — R.O.O.T. receives the template every beat.

    Triplet 396: R input, marker/cursor at C, output at R (cycle
    R -> C -> I). The prior template re-enters here; other input JOINS
    the turning cycle.
    """

    name = "R"

    def telemetry(self):
        # R.intake is TRANSIENT — consumed within the beat and cleared,
        # so it reads 0 between beats and a driver sampling between beats
        # never sees it. My first version watched intake and missed
        # every arrival for exactly that reason.
        #
        # What persists and truthfully signals "R received" is the tick
        # counter: R.O.O.T. receives the prior template EVERY beat, so a
        # tick advancing IS R having received. That is truer to the map
        # than counting a buffer that is emptied before we look. A change
        # in tick = input entered = perception is possible this beat.
        tick = int(getattr(self.c.I, "tick", 0) or 0)
        return tick

    def fire(self) -> dict:
        """Something came through the door. Pass it on — to C and to U.
        Nothing more: R does not judge what came through, only that it
        did.
        """
        return {"module": "R", "came_through": True, "passed_to": ["C", "U"]}
