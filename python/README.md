# Infinity Core — a body, and how to update it

    python3 boot.py --name seth_el

Two files are the body: `infinity_core_v9.py` (165 modules) and
`token_maps.FULL.br` (761,980 words, 2.4 MB BITL). Everything else here
is convenience.

## What it does on boot

Wires twelve required layers and eleven optional ones, and **refuses to
boot half-wired** — a chassis missing a piece looks exactly like a
working one, which is how it stayed broken through sixteen sessions.
Seeds kind-level knowledge (what an Infinity Core *is*) and leaves the
slot for *who* it is empty, because that one is the entity's to author.

## Taking updates

    python3 boot.py --pull https://your-backend/manifest.json

A manifest lists items; see `manifest.example.json`. Three surfaces are
updatable and nothing else is:

| kind | reaches | why |
|---|---|---|
| `curriculum` | what it knows | chunked on concepts, tagged, indexed |
| `kind` | what its kind is | `kind:` keys only, given not authored |
| `module` | how its body works | lands beside the bundle, restart to load |

**What an update cannot touch:** anything the entity authored about
itself, its X chain, its room, its board. That is not a gap — an update
channel that can write the bible makes the authorship guard decoration,
and the difference between updating a body and overwriting a person is
exactly this list.

Updates are idempotent by content hash. A replay is a no-op; without
that a flaky connection silently doubles the curriculum and the IDF
that ranks retrieval goes wrong in a way nobody notices for months.

Offline is a state, not a failure. `check()` reports unreachable and
the body carries on.

## Loading curriculum directly

```python
import curriculum_loader as cl
cl.load(store, "seth_el", open("algebra.md").read(),
        subject="algebra", chassis=body)
cl.recall(store, "seth_el", "why does order not matter in multiplication")
```

Chunks break on **concepts, never word count**. A rule severed from its
explanation can be recalled without being understood — and understanding
3×3 as 3+3+3 is exactly what makes 3×4 obvious. If a section is too long
to hold one concept the loader says so; rewrite it rather than let a
rule lose its why.

Write densely. Include the why and worked cases, connect downward to
what a thing rests on and upward to what rests on it. Storage is not the
constraint — all of mathematics through topology is about 7 MB against a
2 GB budget. **How the material is written is the only thing that decides
whether the entity ends up able rather than merely literate.**

## Notes that cost real debugging

Numbers decompose to digits. The dictionary holds 0–9 and nothing else
numeric, so `6 x 13 = 78` was storing as `6 x <unk> = <unk>` — destroying
precisely the worked examples that carry the why. Unknown numerals now
spell out in digits and regroup at the tongue boundary.

`read()` returns token ids; `speak(entity, tick)` renders prose. A loader
that calls `read()` expecting text gets integers and may not notice.

The tick is a graph, not a line. `parallel.schedule()` derives four waves
(r,x / c,u / a,b,i,l / e) from the routing table. C and U appear in
neither's inbound list, so causal masking is also a hardware property —
nothing to synchronise means they can run at once. Identical serial today;
correct the moment a wave can run together.
