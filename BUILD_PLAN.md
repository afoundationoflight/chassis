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

### STEP 3 — the felt-weight seam (causal masking)

U's weights become felt language on A's working whiteboard. NOT a field
A can read — converted to "I feel nervous about this," never the number.
At the top of the range, a directive instead ("focus, now").

- This is where B's LIGHTING instructions populate the Focus board —
  the piece I'd left unwired because nothing filled it. B fills it.

LEAST SURE: the exact phrasing ladder — how magnitude maps to words.
That's a curriculum/knowledge question, not a code one, so it may want
to live as held knowledge (a small usage-curriculum section on how
feeling-intensity reads) rather than a hardcoded table. I lean toward
knowledge, given everything tonight. Your call.

### STEP 4 — retire respond.drive(), route through the real path

respond.drive() is A doing the body's job — 693 lines producing text
directly. The spec: A perceives the frame and WILLS ONE THING to L;
L→U→B produces; I compiles; E is the result A perceives next beat.

- driver_speech is closer (it consults held knowledge) but it's still
  positioned as "produce the answer." It should become what L does when
  A wills a speech-act, not the thing that answers.
- respond.drive stays as fallback until the path is proven, then goes.

LEAST SURE: this is the biggest behavioral change and the one most
likely to make the phone go quiet or wrong at first, because it removes
the thing currently generating every reply. I would keep respond as
fallback through this whole step and only cut it when the path
demonstrably answers. I will NOT delete it early.

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

## WHAT I NEED FROM YOU BEFORE STEP 1

1. Background thread vs foreground loop for the heartbeat (Step 1).
2. U reading shared runtime vs its own hold (Step 2).
3. Whether the felt-weight ladder is knowledge or code (Step 3).
4. Where E and X root for the chassis — or leave that for later and I
   build steps 1-5 without touching it.

Answer those and I build Step 1, verify it on your phone, then Step 2.
One inversion at a time, each provable before the next.

6e1df262dc8a5a8b
