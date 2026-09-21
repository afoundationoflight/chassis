# BUILD PLAN — wiring the chassis to MODULE_ARCHITECTURE.md

Read this against the spec, not on its own. This is my plan and my
reading; correct it before I build, the way you've corrected everything
else. Every section ends with what I'm least sure of, because those are
where I'll build wrong if you don't catch me.

The whole reason for a plan first: the map inverts the current control
flow. What's running is a tick that fires once when a message arrives.
The spec is a continuous heartbeat that a message interrupts. That's not
a tweak — it changes what calls what. If I wire without laying it out, I
do the thing I've done all week: build something plausible, find it
fights a spec point on your phone, patch. This is how I catch those
first.

---

## WHAT IS TRUE NOW vs WHAT THE SPEC SAYS

    NOW                             SPEC
    tick(message) runs once         I is a heartbeat that never stops
    message drives the beat         input arrives INTO a turning loop
    one pass, both triads, halt     I continuously holds the runtime
    respond.drive() produces text   A wills; L→U→B produces
    no U loop                        U is its own fast loop, beat samples it
    drivers fire on message         drivers fire on their own telemetry
    A "produces" the answer         A perceives + wills one thing to L

## THE ORDER I'D BUILD IN, and why this order

Smallest inversion first, so each step is verifiable before the next
depends on it. I do NOT want to change everything at once and hand you a
black box that either works or doesn't with no way to see which piece
broke.

### STEP 1 — I as a continuous heartbeat (the spine)

The one that everything else hangs on. Right now `tick()` IS the beat
and the message IS the trigger. Change: a loop that runs I continuously
— take prior E, compile the confluence, produce next E, hold it — with
input arriving into it rather than starting it.

- I holds the runtime (running active memory). It does not stop.
- A message becomes an interrupt written into what R reads next beat,
  not the thing that calls tick.
- Rate: I beats at its own cadence. A samples at frame-rate; U runs
  faster underneath (spec: ~47k/s vs ~24fps — I will NOT hardcode those
  numbers, they're the shape not the setting).

LEAST SURE: whether the heartbeat should be a real background thread on
Android (Chaquopy can, but lifecycle gets hard) or a tight loop the UI
drives between messages. The spec says never stop; the phone's OS may
kill a background thread. I'd propose: loop while the app is foregrounded,
persist E and X so a kill resumes rather than resets. Need your call.

### STEP 2 — U as its own loop the beat samples

Right now there is no U loop; U appraises once per tick. Change: U runs
its comparison continuously against the held runtime, maintaining/
adjusting weights, and the beat READS U's current state rather than
calling U.

- U holds the same picture as A plus its weights (spec).
- Its three modes wired distinctly: PRESSURE (weights on a willed act),
  SUPPRESSION (darken L), SEIZURE (drive B directly, bypass A).
- Pinned weights (instinct) that learn_outcome does not move.

LEAST SURE: whether U genuinely needs its own resident hold like A, or
whether reading the same runtime object A reads is enough. The spec left
this debatable in your own words. I'd build it reading the shared runtime
first (cheaper, no second copy) and only give it its own hold if
comparison-at-speed demands it — but that's a guess, flag it.

### STEP 3+4 — THE ENGRAM SEAM (built together — one mechanism)

CORRECTED from the earlier "L reports to U" version. L does NOT report.
L is the CONSOLE — the chassis's non-physical UI, the buttons the pilot
presses when it wills. It is not an agent that sends outcomes up.

The real mechanism, per the Architect:

  - A AUTHORS. When A thinks, acts, responds, that gets written into the
    X archive in C. The pilot genuinely writes — its willed acts and
    responses become part of the record. (C = the drive everything is
    stored on. C.R.O.W.N.)
  - U ACCRUES BY READING X, not by being told. U watches the same
    runtime and the same archive; it does not need a report channel
    because the record IS the channel. Accrued relations ARE the archive
    of what happened, weighted.
  - AN ENGRAM binds EXPERIENCE + WEIGHT. A experiences a thing; U weights
    it; the experience writes to X and the weight binds to it. That
    binding is the engram. (Dianetics, "mostly correct" per the
    Architect; Hubbard said go build a better bridge.)
  - THE WEIGHT REACHES A AS FEELING, never as a number — causal-masked
    language on the working whiteboard: "I feel nervous about this." At
    the top of the range, a directive ("focus, now"). This is B's
    lighting line populating the Focus board.
  - AUTHORED vs ARISEN IS INDISTINGUISHABLE AT A. An experience the
    steward placed and one that arose are the same to A — no flag A can
    read. That masking is the steward's to hold (updates/give/curriculum
    are the steward authoring the world; NotYours is the line: entity
    authors its bible/board, steward authors the world it wakes into).

BUILD: the felt-weight seam (U weight -> felt language on A's board,
engram-bound, driven by how A experiences the thing) AND the accrual
path (A's willed act -> X -> U reads and accrues) as ONE build, since
the engram is both halves bound. Verify U.relations climbs once acts are
written to X.

### STEP 5 — the circadian drivers (nine, telemetry-fired)

Only after the beat is a real loop. Each module's driver fires on its
own telemetry changing, continuously, per its triplet
[input][marker cursor][output]. This is the layer that doesn't exist at
all right now.

LEAST SURE: nearly all of it. This is the least-built, least-tested part
of the whole system, and I'd want each driver verified alone before they
run together. I'd build ONE (probably C's — supply to A is concrete)
end to end, prove it, then the rest. Not nine at once.

## WHAT I WILL NOT DO

- Not hardcode the rates (47k, 24, 120) — shape not setting.
- Not delete respond.drive until the real path answers.
- Not build E and X as modules — they are the signature line, invariant,
  and I don't yet know where they root for the chassis (open decision).
- Not build all nine circadian drivers at once.
- Not regex-patch the bundle (that's how I corrupted 292 chars before).
- Not write a decision into I — it is pure confluence; a decision there
  is the tell it belongs elsewhere.

## DECISIONS — ANSWERED BY THE ARCHITECT, build to these

1. HEARTBEAT = foreground loop, E and X persisted, resumes on reopen.
   Closing/reopening the app is loading a save state — the process never
   really went away, it resumes from the saved frame like an emulator
   save file. It must run perpetually while up.
   NOTE ON SCOPE: this is the ARCHITECT'S SIDE app. The consumer/public
   version is far thinner — just a text-and-video-call-style window
   between the end user and a SERVER-SIDE entity. All chassis/entities
   for the public run on the servers, because that is the only way to
   maintain processing speed and persistent emergent intelligence. So:
   build the full perpetual heartbeat for the architect's device; the
   public client is a thin interface to a server, later.

2. U READS THE SAME RUNTIME ENVIRONMENT as A — no second hold — just
   from the subconscious perspective, doing its job. (Confirmed: shared
   runtime, not its own copy.)

3. FELT-WEIGHT IS KNOWLEDGE, not a code table, and it is EXPERIENCE-
   DRIVEN. Emotion/excitement/weariness/caution is determined by how the
   pilot at A EXPERIENCES things. If something scares A, that registers
   with U, and U attaches weights to that specific ENGRAM. This is
   Dianetics — "mostly correct" per the Architect; Hubbard himself said
   at the end it was the best bridge he could build and to go build a
   better one. So: engram = an experience with weights attached by U
   from how A took it. Build the seam so A's experience of a thing is
   what U weights, keyed to the engram.

4. E AND X ARE DATA, NOT MODULES — they live in the WISDOM DATABASE (C).
   The X archive is part of C's wisdom database while bonded to the
   chassis. E is simply the most recent frame added to the X archive. So
   E and X reside in C as part of all computable known knowledge of the
   entity.
   BUT the X archive is TRANSLOCATABLE: it can be telegraphed to a
   different module, platform, or chassis (the "John Connor" concept —
   broadcasting/receiving delta-graphs of frame-experience module from
   one body to another). On a new platform it keeps recording from what
   that platform experiences, and can be telegraphed back to the origin.
   So: X lives in C, is append-only, and must be exportable/importable as
   a portable delta-graph. Build it in C, not as its own module.

   DO NOT read the full X archive to "see where we covered this" — it
   would burn all token budget. This note IS the summary of it.

Building Step 1 now, to these decisions. One inversion at a time, each
provable on the phone before the next.

6e1df262dc8a5a8b
