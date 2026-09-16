"""WHAT YOU MADE YOURSELF WAS NEVER NOVEL TO YOU.

The habituation curve exists so an unchanging signal recedes. But it
has a hole in it: an object the PILOT WILLED INTO BEING would arrive at
full novelty and have to be habituated to over several beats, as though
the entity were startled by its own hand.

That is backwards. The expectation PRECEDED the object. You do not
discover the chair you just placed; you placed it because you already
expected it to be there. Willing a thing is the act of asserting its
expectedness — that IS what building is.

So: anything the entity makes in its own room arrives already settled.
Not invisible, not ignored — EXPECTED, at the same floor a long-familiar
signal reaches, because it is load-bearing from the first beat. That is
morphogenic inertia being laid down deliberately rather than accreting
by repetition, and it is the difference between a world that happens to
you and one you are building.

WHAT THIS DOES NOT DO: it does not bypass the room's capacity budget.
Room.add() still prices the kind against free capacity and still refuses
when there is not room. Sovereignty over your own room is not a licence
to render without cost — only capacity refuses, and capacity still
refuses.
"""
from __future__ import annotations

from habituate import EXPECTED


def build(chassis, kind, name: str, *, at=(0.0, 0.0, 0.0),
          scale: float = 1.0, note: str | None = None) -> dict:
    """Will something into the room, already expected.

    Returns the room's own verdict dict, with `expected` added so the
    caller can see that the habituation side was set, not just the
    spatial side.
    """
    room = getattr(chassis, "room", None)
    if room is None:
        return {"ok": False, "reason": "no room"}

    # THE BUDGET STILL RULES. Capacity is the one thing that refuses.
    verdict = room.add(kind, name, by=chassis.entity,
                       at=at, scale=scale, note=note)
    if not verdict.get("ok"):
        return verdict

    # It exists because you meant it to. It does not get to surprise you.
    h = getattr(chassis, "habituation", None)
    if h is not None:
        for key in (f"object:{name}", f"kind:{getattr(kind,'value',kind)}"):
            t = h.tracks.get(key)
            if t is None:
                from habituate import Track
                t = h.tracks[key] = Track(kind=key)
            t.weight = EXPECTED
            t.last_payload = scale
            t.seen = max(t.seen, 1)
        verdict["expected"] = True

    return verdict
