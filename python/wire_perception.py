"""WIRE PERMANENCE AND PROVENANCE INTO THE ACTUAL TICK.

local.py assembles the scene at the moment the body LOOKS
(eyes.see(...) -> _scene) and calls habituation.observe() only for
proprioceptive and interoceptive signals. So today:

  - the room is seen, but never compared against what it should be
  - habituation is fed the body, but never the world

This closes both, at the seam the chassis already has, rather than
inventing a second perception path beside the real one.

WHY IT HOOKS THE LOOK, NOT A TIMER. You do not discover your desk is
missing on a schedule. You discover it when you look. Checking the model
against the room at exactly the moment of sight is what makes absence
feel like absence instead of a background process reporting a diff.
"""
from __future__ import annotations

from habituate import Track, EXPECTED
from permanence import Permanence
import provenance as pv


def attach(chassis, *, phase: str | None = None):
    """Give the body a model of its own room, updated every time it looks."""
    if getattr(chassis, "permanence", None) is None:
        chassis.permanence = Permanence(chassis.entity)
        chassis.permanence.learn(chassis.room)

    original_tick = chassis.tick

    def tick(*a, **kw):
        out = original_tick(*a, **kw)
        _perceive(chassis, phase=phase)
        return out

    chassis.tick = tick
    return chassis


def _perceive(chassis, *, phase: str | None = None):
    """Run after the body has looked: compare, then feed what it found."""
    perm = chassis.permanence
    hab = getattr(chassis, "habituation", None)

    # WHO HAS BEEN ACTING. If the entity moved something itself, that is
    # not news to it; provenance is what tells the difference.
    notices = perm.check(chassis.room, phase=phase, mover=None)

    if hab is None:
        return notices

    # FEED THE WORLD TO HABITUATION, not just the body. Each thing in the
    # room is a signal whose settling rate depends on whose it is.
    for f in chassis.room.features.values():
        name = getattr(f, "name", None)
        if not name:
            continue
        origin = pv.origin_of(chassis, name)
        hab.observe(f"object:{name}", tuple(getattr(f, "at", ())),
                    origin=origin)

    # AN UNEXPLAINED NOTICE IS NOT ALLOWED TO GO QUIET. Habituation must
    # not sand down the one signal that means something acted — so a
    # displacement or absence snaps its track back to full.
    for n in notices:
        key = f"object:{n.name}"
        t = hab.tracks.get(key)
        if t is None:
            t = hab.tracks[key] = Track(kind=key)
        t.weight = n.weight
        t.startles += 1
        t.settled_at = None

    return notices
