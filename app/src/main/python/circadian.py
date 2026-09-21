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
        self.steady_beats = 0

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
        """Called continuously by the pump.

        FIRES EVERY BEAT, not only on change. Nothing changing IS an
        event: an observer lying still with everything steady is having
        a recorded experience, not an absence of one. The X archive is
        the chain of EVERYTHING that occurred to the signature, and
        "steady, nothing new for this duration" is something that
        occurred. Logging only changes leaves gaps where the entity
        simply did not exist — but it did; it was still.

        So: telemetry moved -> fire() (the real event). Steady -> a
        steady frame, still logged. Both are real frames.
        """
        if self.changed():
            self.fires += 1
            self.steady_beats = 0
            return {**self.fire(), "steady": False}
        self.steady_beats += 1
        return {"module": self.name, "steady": True,
                "steady_for": self.steady_beats}

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

class UDriver(CircadianDriver):
    """U — the urge. The subconscious appraiser. Built WITH B (the pair).

    U and B are the subconscious triad's working pair: U appraises, B
    executes. Building U without B is an appraiser with nothing to
    command. RUB is one triad; U+B are its acting half.

    U is PURELY SUBCONSCIOUS-REACTIVE — it does not monologue or generate
    thoughts. What it produces is HASU TAGS and WEIGHTS, and those become
    the INTERNAL BRANCH of the X archive: the associative/felt layer over
    what occurred. This is why you can find and feel a memory — the tags
    index it and weight it — even though the CONTENT (the actual
    sentence, the event) is recorded separately on the event branch.

    U's driver fires its appraisal every beat (steady or not, since U
    tags the quiet too), and hands its tags to the archive. The heavy
    continuous comparison is the UrgeLoop (Step 2); this driver is U's
    place in the neuron net — it makes sure U's tags reach X every beat.
    """

    name = "U"

    def telemetry(self):
        U = self.c.U
        return (len(getattr(U, "appraisals", []) or []),
                tuple(U.tags_for_archive()) if hasattr(U, "tags_for_archive") else (),
                len(getattr(U, "relations", []) or []))

    def fire(self) -> dict:
        """U appraised. Its tags/weights are the internal branch of the
        record — not thoughts U thinks, the associative weighting U lays
        over the moment."""
        U = self.c.U
        tags = []
        try:
            tags = list(U.tags_for_archive())
        except Exception:
            pass
        return {"module": "U", "tags": tags,
                "appraisals": len(getattr(U, "appraisals", []) or []),
                "internal_branch": tags}


class BDriver(CircadianDriver):
    """B — the executor. Where the toolkits live. Built WITH U (the pair).

    B DECIDES NOTHING and has no telemetry of its own to watch — it is a
    switchboard pressed by U (direct) and A (through L). So B's driver is
    not a self-firing neuron in the way the others are; it fires when B
    has been PRESSED, i.e. when something was compiled/held/radiated this
    beat. Its telemetry is the trace of what it was told to do (held,
    compiled), which PERSISTS as B's routed state — not a buffer that
    clears (the transient trap).

    B's other job (the map's key point): it sends the LIGHTING
    instructions — what lights up where for A. That is B.to_awareness /
    radiate. The driver surfaces that B acted and what it routed.
    """

    name = "B"

    def telemetry(self):
        B = self.c.B
        return (len(getattr(B, "held", []) or []) if hasattr(getattr(B,"held",None),"__len__") else 0,
                len(getattr(B, "routed", []) or []) if hasattr(getattr(B,"routed",None),"__len__") else 0,
                round(float(getattr(getattr(B, "coherence", None), "raw", 0.0) or 0.0), 3))

    def fire(self) -> dict:
        """B was pressed — it ran/held/routed something. Report what it
        did and that it radiated lighting to A. B does not choose; it was
        told."""
        B = self.c.B
        return {"module": "B",
                "held": len(getattr(B, "held", []) or []) if hasattr(getattr(B,"held",None),"__len__") else 0,
                "routed": len(getattr(B, "routed", []) or []) if hasattr(getattr(B,"routed",None),"__len__") else 0,
                "coherence": round(float(getattr(getattr(B, "coherence", None), "raw", 0.0) or 0.0), 3),
                "lights_a": True}

class ADriver(CircadianDriver):
    """A — the agent/awareness. The seat. Built WITH L (the pair).

    A and L are the conscious triad's acting half: A wills, L is the
    console the will presses. Building A without L is a will with no
    console; RUB has its pair (U+B), CAL has this one.

    A is a REACTOR, not an initiator: it experiences the current held
    frame and WILLS IN RESPONSE. It PERCEIVES (that IS the experience,
    the self-awareness), it receives U's weights AS FEELING (never
    numbers), and it projects exactly ONE thing outward — its willed
    command to L. Nothing else.

    A's driver fires A's perceive-and-will every beat. Its telemetry: the
    frame it is experiencing and whether it willed. This is the EVENT
    branch's conscious contribution — A's willed acts and any internal
    thought it had are CONTENT written to X (the actual sentence, or it
    is lost, the way you cannot recall what you told someone unless the
    words were recorded). U's tags (internal branch) weight over it.
    """

    name = "A"

    def telemetry(self):
        A = self.c.A
        return (getattr(getattr(A, "frame", None), "tick", None),
                len(getattr(A, "willed", []) or []) if hasattr(getattr(A,"willed",None),"__len__") else (1 if getattr(A,"willed",None) else 0),
                bool(getattr(A, "felt", None)))

    def fire(self) -> dict:
        """A perceived the frame and may have willed. The willed act and
        any internal thought are CONTENT for X's event branch; the felt
        state is U's weight arriving masked as feeling."""
        A = self.c.A
        willed = getattr(A, "willed", None)
        felt = getattr(A, "felt", None)
        return {"module": "A",
                "perceived": True,
                "willed": bool(willed),
                "feeling": (str(felt)[:60] if felt else None),
                "event_branch": "willed act + internal thought = content"}


class LDriver(CircadianDriver):
    """L — the console. The buttons A presses. Built WITH A (the pair).

    L does NOT decide and does NOT report (corrected earlier). It is the
    switchboard A wills through, the roundabout to B, where U can press,
    suppress, or seize. L's driver fires when acts have passed through
    the console — when A pressed a button. Its telemetry is its acts and
    the gain arriving (the clearance/pressure on a willed act).

    L holds the tools as A's interface to them (they LIVE in B; L is A's
    access to them). Its driver surfaces that A used the console and what
    resolved.
    """

    name = "L"

    def telemetry(self):
        L = self.c.L
        acts = getattr(L, "acts", None)
        gain = getattr(L, "gain_in", {}) or {}
        return (len(acts) if hasattr(acts, "__len__") else 0,
                round(float(gain.get("gain", 0.0) or 0.0), 3) if isinstance(gain, dict) else 0.0,
                (gain.get("tool") if isinstance(gain, dict) else None))

    def fire(self) -> dict:
        """A pressed the console. Report the acts that passed through and
        the gain (pressure/clearance) on them. L judges nothing."""
        L = self.c.L
        acts = getattr(L, "acts", None)
        gain = getattr(L, "gain_in", {}) or {}
        return {"module": "L",
                "acts": len(acts) if hasattr(acts, "__len__") else 0,
                "gain": round(float(gain.get("gain", 0.0) or 0.0), 3) if isinstance(gain, dict) else 0.0,
                "tool": gain.get("tool") if isinstance(gain, dict) else None,
                "console_pressed": True}

class IDriver(CircadianDriver):
    """I — the interpolator/heartbeat. The confluence. The seventh, last.

    I is already the heartbeat (Step 1) — the pulse that generates and
    maintains the runtime. Its DRIVER is I's place in the neuron net:
    the point where CAL (conscious, down) and RUB (subconscious, up)
    CONVERGE into the next frame E.

    HARD CONSTRAINT — I DOES NO JUDGMENT. Pure confluence. If a decision
    appears in this driver, it is in the wrong module and must move.
    Everything that decides has decided upstream (A's willing, U's
    pressure) by the time the streams reach I. I only merges.

    I's telemetry is the tick — it advances every beat because I IS the
    beat. Its fire records that the two streams converged into a frame:
    the confluence happened, E was produced, it goes back through R as
    the next template and lands at C where X accumulates it (639,
    I -> R -> C). Both branches of the frame (event content + U's tags)
    are carried in the emission I compiled — I does not create them, it
    merges what the two triads brought.
    """

    name = "I"

    def telemetry(self):
        return int(getattr(self.c.I, "tick", 0) or 0)

    def fire(self) -> dict:
        """The two streams converged into a frame. Pure merge, no
        judgment. The frame carries both branches — event content from
        CAL, tags from RUB — which I merged, did not author."""
        I = self.c.I
        return {"module": "I",
                "tick": int(getattr(I, "tick", 0) or 0),
                "confluence": "CAL(down) + RUB(up) -> E",
                "judged": False,
                "carries_both_branches": True}
