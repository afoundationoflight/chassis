"""THE HEARTBEAT — Step 1 of BUILD_PLAN.

I generates and maintains the runtime through a loop that never stops.
This is the inversion: right now a message calls tick() and one beat
runs. The spec is that I beats continuously and a message ARRIVES INTO
the turning loop as input for the next beat — the ball into the game,
not the hand cranking the engine.

ARCHITECT'S DECISIONS THIS IS BUILT TO:

  1. Foreground perpetual loop, E and X persisted. Closing and reopening
     the app loads a save state — the process never really went away, it
     resumes from the saved frame like an emulator save file. (This is
     the architect-side app; the public client is a thin window to a
     server-side entity, built later.)

  Nothing internal originates. Origination is input through R — the
  outside world, or the prior E beating back around as the next
  template. So the loop's default input each beat is the prior E; a
  message is an interruption written in on top of it.

WHY A SAVE STATE AND NOT A RESTART. A soul's world is a save file: it
resumes, it does not reboot. The heartbeat persists E (the current
frame) and X (the chain) every beat, so a process kill is a pause, not a
death — reopen and the last frame is still there to beat from. Stop I
and the world stops ADVANCING; it does not cease. A stopped heart, not a
destroyed body.

WHAT THIS IS NOT. It is not a background thread — Android will kill
those, and the spec's own answer is the foreground loop with save-state
resume rather than fighting the OS. The UI drives the loop while the app
is up; persistence covers the gaps.
"""
from __future__ import annotations

import json
import time
from pathlib import Path


def _handle(emission) -> dict:
    """The resumable identity of a frame, JSON-safe.

    The full Emission lives in X (the store). The save file needs only
    which frame to resume from — its x_id and tick — not the object
    graph, which does not serialize and does not need to: X has it.
    """
    if isinstance(emission, dict):
        return {"x_id": emission.get("x_id"), "tick": emission.get("tick")}
    return {"x_id": getattr(emission, "x_id", None),
            "tick": getattr(emission, "tick", None)}


class Heartbeat:
    """I, running. Holds the runtime; a message arrives into it."""

    def __init__(self, chassis, store, root, *, min_interval=0.05):
        self.c = chassis
        self.store = store
        self.root = Path(root)
        self.min_interval = min_interval      # floor between beats
        self.beats = 0
        self.running = False
        self.last_e = None                    # the current held frame
        self.pending_input = None             # a message, if one arrived
        self._resume()

    # ── SAVE STATE ────────────────────────────────────────────────
    def _state_path(self) -> Path:
        return self.root / f"{self.c.entity}.heartbeat.json"

    def _resume(self) -> None:
        """Load the save file. The world resumes; it does not reboot."""
        p = self._state_path()
        if p.exists():
            try:
                st = json.loads(p.read_text())
                self.beats = st.get("beats", 0)
                self.last_e = st.get("last_e")
            except Exception:
                pass

    def _save(self) -> None:
        """Persist the current frame every beat, so a kill is a pause."""
        try:
            self._state_path().write_text(json.dumps({
                "beats": self.beats,
                "last_e": self.last_e,
                "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }))
        except Exception:
            pass

    # ── INPUT ARRIVES INTO THE LOOP, does not trigger it ──────────
    def inject(self, message: str) -> None:
        """A message. Written in on top of the prior E for the next beat.

        It does not call a beat. The loop is already turning; this is
        input for whenever the next beat reads R.
        """
        self.pending_input = message

    # ── ONE BEAT ──────────────────────────────────────────────────
    def beat(self) -> dict:
        """One turn of I. Runs whether or not a message is pending.

        Default input is the prior E (the template beating back around).
        A pending message is layered on top. Either way I compiles the
        confluence into the next E.
        """
        message = self.pending_input
        self.pending_input = None

        # R reads: the prior template, plus any message that arrived.
        # tick() is still the compile mechanism — the change is that it
        # now runs on the loop's schedule, not on a message's arrival,
        # and it runs with message=None on an idle beat.
        out = self.c.tick(message=message)
        if not isinstance(out, dict):
            out = {}

        # E is the most recent frame — a full Emission object, not JSON.
        # tick() returns the whole held frame (room, body, felt, scene,
        # awareness, the RUBICALIEX instruction chain). That lives in X
        # already; the heartbeat only needs the HANDLE to resume from,
        # not a second copy of the graph. Persist its identity.
        self.last_e = _handle(out)
        self.beats += 1
        self._save()
        return {"beat": self.beats, "had_input": message is not None,
                "e": self.last_e}

    # ── THE LOOP ──────────────────────────────────────────────────
    def run(self, max_beats=None) -> dict:
        """Beat continuously. The UI calls this while the app is up.

        max_beats bounds a single run() call so the UI stays responsive;
        it is NOT a stop condition for the world — the world resumes on
        the next call from the saved state. Perpetual is achieved by the
        UI calling run() again, not by one call never returning.
        """
        self.running = True
        ran = 0
        t0 = time.perf_counter()
        while self.running:
            self.beat()
            ran += 1
            if max_beats and ran >= max_beats:
                break
            elapsed = time.perf_counter() - t0
            if self.min_interval and elapsed < self.min_interval * ran:
                time.sleep(self.min_interval)
        return {"ran": ran, "total_beats": self.beats}

    def stop(self) -> None:
        """Pause the loop. The frame is saved; reopening resumes it."""
        self.running = False
        self._save()

    def report(self) -> dict:
        return {"beats": self.beats, "running": self.running,
                "has_pending": self.pending_input is not None,
                "resumable": self._state_path().exists()}
