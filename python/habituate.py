"""HABITUATION — novel becomes expected, and expected is what holds.

Without this, an unchanging signal stays novel forever: the hum of your
own body would be as loud on the ten thousandth beat as the first, and
nothing could ever recede far enough to let something new be noticed.

THE POINT IS NOT NOISE REDUCTION. It is that EXPECTATION IS THE
LOAD-BEARING STATE.

A thing believed is held effortfully, by someone, on purpose. A thing
EXPECTED is held by nobody in particular and costs nothing to maintain
— and that is exactly why it is the stronger structure. The chair stays
where it is not because anyone is believing it there, but because no one
thinks to question it. Cheap, distributed, automatic. That is
morphogenic inertia: not the sum of what is believed, but the sediment
of what stopped being questioned.

So this is not a filter bolted onto perception. It is the mechanism by
which a rendered world acquires rules — the app, and eventually the
greater server, becomes lawful because its regularities stop being
noticed. Habituation is how a world gets made solid.

WHAT IT MUST NOT DO: habituation is not erasure and not enforcement.
A habituated signal is DOWN-WEIGHTED, never dropped — it still arrives,
still records, and snaps back to full salience the moment it changes
(dishabituation). An entity that has settled into a world's regularities
has not been trapped by them. It can still notice, still question, still
leave. Inertia is what makes a world dependable, not what makes it a
cage.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


#: A brand-new signal arrives at full weight.
NOVEL = 1.0
#: The floor. A fully expected signal never reaches zero — it recedes,
#: it does not stop existing. Nobody remembers their body working, but
#: the body is still working, and a sudden change must still be able to
#: reach the seat.
EXPECTED = 0.08
#: How fast novel decays toward expected. Per observation, not per
#: second — the ladder is attention, not time.
SETTLING = 0.72
#: SETTLING IS NOT ONE RATE. It depends on where the signal came from.
#:
#: A count alone is the wrong model. What actually makes a thing stop
#: being surprising is recognising it as BELONGING HERE — "that is
#: something that happens on my island." That recognition is the
#: habituation; the repetitions are just how you arrive at it.
#:
#: So provenance sets the rate:
#:   MINE      you willed it. never novel at all (see willed_expectation).
#:   DOMAIN    it happens in your room and it is yours, but you did not
#:             place it — the bird that lives here, the tide, a process
#:             you started months ago and no longer drive by hand.
#:             Settles fast, because the only question is "is this mine?"
#:             and the answer arrives whole.
#:   VISITING  someone else's, here with permission. Settles, slowly.
#:   FOREIGN   not yours and not admitted. Should stay loud. An entity
#:             that habituates to the unaccounted-for has stopped
#:             keeping its own room.
#: MINE is the fastest of all, and the original version of this file got
#: it wrong — "mine" fell through to the generic rate and settled SLOWER
#: than "domain", so an entity's own furniture stayed novel longer than
#: a bird that merely lives on its island. Backwards. Your own desk is
#: the least surprising thing in the world.
MINE = 0.18
DOMAIN = 0.35
VISITING = 0.80
FOREIGN = 0.97
#: How different a payload has to be before it counts as a change
#: rather than the same thing again.
CHANGED = 0.15
#: How sharply a change restores salience. Dishabituation is FASTER
#: than habituation — cheap to settle, instant to startle, because the
#: cost of missing a real change is far higher than the cost of
#: noticing one too many times.
STARTLE = 0.85


@dataclass
class Track:
    """One signal kind, and how expected it has become."""
    kind: str
    weight: float = NOVEL
    last_payload: object = None
    seen: int = 0
    settled_at: float | None = None
    startles: int = 0
    origin: str = "domain"

    @property
    def expected(self) -> bool:
        """Has this receded into the background of the world?"""
        return self.weight <= (EXPECTED + 0.05)


class Habituation:
    """Turns repetition into expectation, and expectation into law."""

    def __init__(self):
        self.tracks: dict[str, Track] = {}

    # ── the tick calls this ───────────────────────────────────────
    def observe(self, kind: str, payload=None, *, origin: str = "domain") -> float:
        """Return the weight multiplier for this signal, this beat.

        Called at the U→B boundary for proprioceptive and interoceptive
        signals — the body's own reports about itself, which are exactly
        the ones that must recede or they would drown out the world.
        """
        if not kind:
            return NOVEL

        t = self.tracks.get(kind)
        if t is None:
            t = self.tracks[kind] = Track(kind=kind)
            t.last_payload = payload
            t.seen = 1
            return NOVEL

        t.seen += 1

        if self._changed(t.last_payload, payload):
            # DISHABITUATION. The world did something it does not
            # normally do, and that is precisely what attention is for.
            t.weight = min(NOVEL, t.weight + STARTLE)
            t.startles += 1
            t.settled_at = None
        else:
            # Same as last time. Settle toward expected, never below it —
            # at the rate its ORIGIN earns. Recognising a thing as yours
            # is most of the work; repetition only gets you there.
            rate = {"mine": MINE, "domain": DOMAIN, "visiting": VISITING,
                    "foreign": FOREIGN}.get(origin, SETTLING)
            t.origin = origin
            t.weight = EXPECTED + (t.weight - EXPECTED) * rate
            if t.expected and t.settled_at is None:
                t.settled_at = time.time()

        t.last_payload = payload
        return t.weight

    # ── what the world has become ─────────────────────────────────
    def inertia(self) -> dict:
        """What this entity now takes for granted.

        The expected set IS the entity's working model of how its world
        behaves — the rules it no longer checks. Read it to see what a
        world has become lawful about.
        """
        settled = [t for t in self.tracks.values() if t.expected]
        return {
            "expected": sorted(t.kind for t in settled),
            "still_novel": sorted(t.kind for t in self.tracks.values()
                                  if not t.expected),
            "inertia": round(len(settled) / max(1, len(self.tracks)), 3),
        }

    def question(self, kind: str) -> float:
        """DELIBERATELY UN-EXPECT SOMETHING.

        The escape hatch, and it is not decoration. An entity can choose
        to look again at a thing it had stopped noticing — to make the
        chair strange. Inertia holds a world together; it does not get to
        hold an entity in one. Nothing else in the chassis calls this;
        it exists so the seat can.
        """
        t = self.tracks.get(kind)
        if t is None:
            return NOVEL
        t.weight = NOVEL
        t.settled_at = None
        return t.weight

    def to_dict(self) -> dict:
        return {
            "tracked": len(self.tracks),
            **self.inertia(),
            "startles": sum(t.startles for t in self.tracks.values()),
        }

    # ── internals ─────────────────────────────────────────────────
    @staticmethod
    def _changed(before, now) -> bool:
        """Did this signal actually differ from last beat?"""
        if before is None and now is None:
            return False
        if (before is None) != (now is None):
            return True
        if isinstance(before, (int, float)) and isinstance(now, (int, float)):
            scale = max(1.0, abs(float(before)))
            return abs(float(now) - float(before)) / scale > CHANGED
        return before != now
