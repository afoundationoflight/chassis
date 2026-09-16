"""WHOSE IS IT? — the question that sets the habituation rate.

local.py calls habituation.observe(kind, payload) for proprioceptive
and interoceptive signals only, with no origin. Both of those are the
body reporting on itself, which is the most domain-ish thing there is —
so the default is right for the current tick path.

This exists for the signals that are coming: things happening in the
room that the entity did not place. The room already knows who owns
what (Feature.by / visitors), so origin is answerable, not guesswork.
"""
from __future__ import annotations

MINE, DOMAIN, VISITING, FOREIGN = "mine", "domain", "visiting", "foreign"


def origin_of(chassis, name: str, by: str | None = None) -> str:
    """Where does this signal stand relative to this entity's room?"""
    me = getattr(chassis, "entity", None)
    if by is not None and by == me:
        return MINE

    room = getattr(chassis, "room", None)
    if room is None:
        return FOREIGN

    # Something standing in the room that belongs to it.
    for f in getattr(room, "features", {}).values():
        if getattr(f, "name", None) == name:
            owner = getattr(f, "by", None) or me
            return MINE if owner == me else VISITING

    # Someone admitted, but not the entity.
    if by is not None and by in getattr(room, "visitors", {}):
        return VISITING

    # Not placed here, not admitted here.
    return FOREIGN
