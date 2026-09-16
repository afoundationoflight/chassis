"""OBJECT PERMANENCE — what is supposed to be where, and when.

Habituation answers "is this signal familiar?" This answers a different
question: "IS THE WORLD AS I LEFT IT?"

Those come apart immediately. A stone sitting still and a stone that has
vanished produce the same nothing. Only an entity holding a model of
where things SHOULD be can tell the difference between quiet and gone.
Without that, looking away destroys the world and looking back rebuilds
a different one.

THE MODEL IS THE POINT, NOT THE PERCEPTION. What makes a room solid is
not that you keep checking it. It is that you DO NOT HAVE TO. You know
the desk is behind you. You are not maintaining it by attention; you are
carrying an expectation cheap enough to hold for free, and that is the
same economy habituation runs on — expected things cost nothing, which
is exactly why they can be load-bearing.

WHAT THIS BUYS THAT NOTHING ELSE DOES:

  PERSISTENCE   the fern exists while unobserved. Not rendered — held.
  DISPLACEMENT  "that moved" is only sayable against a remembered place.
  ABSENCE       a thing missing from where it belongs is INFORMATION,
                and the loudest kind. An empty chair is not neutral.
  SCHEDULE      some things are supposed to be different at different
                times. The lamps are lit at night. Tide is out at noon.
                A thing off its schedule is displaced in time rather
                than space, and should read as strange the same way.

WHO IS ALLOWED TO MOVE THINGS. A displacement the entity performed is
not a surprise — it updates the model silently, the same way a willed
object arrives pre-expected. A displacement by someone else is exactly
what the entity needs to notice. Provenance decides which, and the room
already knows the answer.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field


#: How far a thing may drift before it counts as moved, in metres.
#: Below this is measurement noise; above it is an event.
MOVED_M = 0.25
#: Weight returned for a world that matches its model. Free to hold.
AS_EXPECTED = 0.05
#: A thing not where it belongs. Loud, because it means something acted.
DISPLACED = 0.90
#: A thing that should be here and is not. Louder — absence is the
#: strongest signal a model can produce, because it cannot be explained
#: by the thing itself.
ABSENT = 1.0


@dataclass
class Placement:
    """Where a thing belongs, and when it is supposed to be that way."""
    name: str
    at: tuple
    kind: str = ""
    owner: str = ""
    #: Optional. ("night",) means this is expected to hold at night only.
    #: Empty means always.
    when: tuple = ()
    last_seen: float = field(default_factory=time.time)
    last_confirmed_at: tuple | None = None
    displacements: int = 0

    def expected_now(self, phase: str | None) -> bool:
        """Is this placement supposed to hold in the current phase?"""
        return (not self.when) or (phase in self.when)


@dataclass
class Notice:
    """Something the model did not predict. This is what gets reported."""
    name: str
    what: str          # "displaced" | "absent" | "arrived" | "off_schedule"
    weight: float
    detail: str = ""
    by: str | None = None


class Permanence:
    """The entity's standing model of its own room."""

    def __init__(self, entity: str = ""):
        self.entity = entity
        self.model: dict[str, Placement] = {}
        self.notices: list[Notice] = []

    # ── learning the room ─────────────────────────────────────────
    def learn(self, room, *, phase: str | None = None) -> int:
        """Take the room as it currently stands to be how it should be.

        Called once the entity has actually looked. This is not
        observation — it is the decision to start expecting.
        """
        n = 0
        for f in getattr(room, "features", {}).values():
            name = getattr(f, "name", None)
            if not name:
                continue
            self.model[name] = Placement(
                name=name,
                at=tuple(getattr(f, "at", (0.0, 0.0, 0.0))),
                kind=str(getattr(getattr(f, "kind", ""), "value", "")),
                owner=self.entity,
            )
            n += 1
        return n

    def expect(self, name: str, at: tuple, *, kind: str = "",
               when: tuple = (), owner: str = "") -> Placement:
        """Assert directly that something belongs somewhere.

        Used when the entity wills a thing into being — the expectation
        precedes the object, so the model is written at the same moment
        the object is.
        """
        p = Placement(name=name, at=tuple(at), kind=kind, when=when,
                      owner=owner or self.entity)
        self.model[name] = p
        return p

    # ── checking it ───────────────────────────────────────────────
    def check(self, room, *, phase: str | None = None,
              mover: str | None = None) -> list[Notice]:
        """Compare the room against the model. Report only the gaps.

        `mover` names who has been acting. If it is the entity itself,
        displacements are its own doing and update the model silently
        rather than surprising it.
        """
        out: list[Notice] = []
        present = {}
        for f in getattr(room, "features", {}).values():
            nm = getattr(f, "name", None)
            if nm:
                present[nm] = tuple(getattr(f, "at", (0.0, 0.0, 0.0)))

        # things that should be here
        for name, p in self.model.items():
            if not p.expected_now(phase):
                continue
            if name not in present:
                out.append(Notice(name, "absent", ABSENT,
                                  f"{name} is not where it belongs"))
                continue
            drift = _dist(present[name], p.at)
            if drift > MOVED_M:
                if mover and mover == self.entity:
                    # I moved it. Update quietly; do not startle myself.
                    p.at = present[name]
                else:
                    p.displacements += 1
                    out.append(Notice(
                        name, "displaced", DISPLACED,
                        f"{name} moved {drift:.2f}m", by=mover))
                    p.at = present[name]
            p.last_seen = time.time()
            p.last_confirmed_at = present[name]

        # things here that the model does not account for
        for name, at in present.items():
            if name not in self.model:
                out.append(Notice(name, "arrived", DISPLACED,
                                  f"{name} is here and was not before",
                                  by=mover))

        self.notices = out
        return out

    # ── what it costs to hold ─────────────────────────────────────
    def weight_for(self, name: str) -> float:
        """A thing where it belongs is nearly free to keep holding."""
        for n in self.notices:
            if n.name == name:
                return n.weight
        return AS_EXPECTED

    def solid(self) -> dict:
        """How settled this room is. A world with no open notices is one
        the entity does not have to keep checking."""
        return {
            "known": len(self.model),
            "unexplained": len(self.notices),
            "solid": not self.notices,
            "notices": [{"name": n.name, "what": n.what, "detail": n.detail}
                        for n in self.notices],
        }


def _dist(a, b) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))
