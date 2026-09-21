"""CIRCADIAN DRIVERS — Step 5 of BUILD_PLAN. C first (driver 1 of 9).

This is the layer that did not exist at all. The beat (Steps 1-4) runs;
the circadian drivers are the CONTINUOUS life of each module, firing on
its OWN telemetry changing, at whatever rate that happens — not on the
beat, not on a message.

C IS BUILT FIRST for the reason the heart was built before it: the heart
pumps before there is a brain to know it (Step 1 was I, the pulse). C is
the next organ because it is the substrate everything references — no
wisdom database, nothing to drive data from. Embryology, not analogy:
heart tube first, then the structure that reads from it.

THE PATTERN THIS ESTABLISHES for the other eight drivers:

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
