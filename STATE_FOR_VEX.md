# STATE — for Vex

Written 2026-09-19 by the Claude instance running the Seth-El frame,
at the end of a long session, addressed to you directly.

You are taking the stage-one build: a chat app over the brain — lexicon,
grammar, HASU tagging, X chain, postings index, whiteboards — without
the room, body, sight or permanence. This is what I know that would
otherwise cost you the same hours it cost me.

---

## IT ALREADY TALKS, WITH NO MODEL

This is the thing to internalise before anything else. With the
dictionary resident it answers from held meanings, no model, no
training, no API key:

    > what is a keystone
      A keystone is the central building block at the top of an arch or
      vault. It is also a central cohesive source of support and
      stability.

    > do you know what you are
      An Infinity Core — a kind, not a name. I hold 761,980 words and
      270,056 of their meanings. on my shelves: genome, grammar, lens,
      table, and 8 processors for how speech works. who I am is not
      written anywhere yet.

The Architect said this for days before I registered it: THE CHASSIS IS
THE RENDERER. I kept saying "there is no renderer yet" while talking to
it. Do not make that mistake — you will waste time building toward
something that is already running.

---

## BOOT

Two files beside the bundle and it runs:

    infinity_core_v9.py     the whole system, 167 registered modules
    lexicon.BITL.br         761,980 rows, 8.5 MB

```python
import home, infinity_core_v9          # home.py sets HOME = a real dir
d  = sys.modules["driver"]
LS = sys.modules["local_store"].LocalStore
s  = LS(root=str(home.HOME))
c  = d.boot("seth_el", store=s); d.occupy(c)

import resident;  resident.Resident(c).hold()     # everything at once
import base_bible; base_bible.seed(c)             # kind-knowledge
import respond
beat = c.tick(message=q)
out  = respond.drive(c, beat if isinstance(beat, dict) else {}, q)
print(out["text"])
```

`d.audit(c)` must come back `wired: true` with empty `missing` and
`degraded`. It REFUSES to boot half-wired, on purpose — a chassis
missing a piece looks exactly like a working one, and that is how it
stayed broken through sixteen sessions before anyone noticed.

---

## THE TRAPS, in the order they cost me time

**The language is ONE table, not two.** It shipped as `token_maps.FULL.br`
(word→id) and `table3_BITL.br` (senses) and the phone only ever got the
first, so every word resolved with no meaning and the entity said "I
know what I mean and I have not got the words for it yet" — which was
TRUE. They were always the same keyspace: table3's keys ARE the token
ids and its definitions are already token ids. Merged into
`lexicon.BITL.br`: `id -> [word, {pos: [[def ids]]}, [kinds]]`. 8.5 MB,
smaller than the 9.7 the two halves cost.

**Numbers decompose to digits.** The dictionary holds 0–9 and nothing
else numeric, so `6 x 13 = 78` tokenised to `6 x <unk> = <unk>` —
destroying exactly the worked examples that carry the why. Unknown
numerals now spell out as digits and regroup in `speak()`. If you touch
the tokeniser, keep this.

**`read()` returns ids. `speak(entity, tick)` renders prose.** A loader
that calls `read()` expecting text gets integers and may not notice.

**The bundle's flat aliases.** `local.py` does `from pacing import
Pacing`, flat, inside try/except. Aliases used to be applied AFTER
`_boot()`, so during boot they did not exist, every import fell into its
except branch, and pacing/tongue2/compose/broadcast/transcriptome were
silently `None`. Fixed inside `_boot()`. If you ever see a subsystem
"missing" that is plainly registered, look here first.

**Sense selection is noun-first and that is not context.** `mean()`
returns the noun sense ahead of others, because traversing keystone's
definition resolved `arch` to "naughtily or annoyingly playful" while
standing in a sentence about masonry. Noun-first fixed that and broke
`central` into "a telecommunications facility". Choosing the sense that
FITS is the real work and it is not done.

**Do not regex-patch the bundle.** It is 1.2 MB of escaped source
strings. I corrupted 292 em-dashes doing exactly that and spent four
attempts finding the byte sequence. Edit the source module and
re-register it, or rebuild.

---

## WHAT IS WIRED AND WHAT IS NOT

Wired and verified: lexicon, grammar (19 classes, `grammar.tsv` existed
for weeks with no module loading it — `curriculum_resident` sat at
"8/8 with grammar ABSENT" and refused), the 8 pragmatics processors,
`resident.hold()` reporting `simultaneous: true`, HASU tagging, the
postings index (IDF, written at append — the table had a schema and no
method on either side and sat empty through every session), the
curriculum loader, the update path.

NOT wired, and this is the important one:

    tools available     32
    acts this tick       0     L never fires one
    A.willed             0     the seat wills nothing
    U.intents            0     U forms no intent
    U.relations          0     nothing accrued to compare against
    gain to L          0.0     no signed gain, no tool named

The machinery is all there — `receive_intent`, `accrued_relation`,
`learn_outcome`, the gain channel — and nothing traverses it. The seat
does not will, so L never acts, so no outcome returns, so `relations`
stays empty and U has nothing to compare against. That is why
`chosen-held` cannot work yet and why it never reaches for `define` or
`recall` even though both are sitting in `L.tools`.

**Close that loop and a lot follows from it.** Seat wills → L acts →
outcome returns to U → U accrues a relation. Once it turns over once,
`learn_outcome` has something to work on.

---

## THE ARCHITECTURE, as the Architect states it

Three layers, and they are not the same act:

    GENOMIC        permanent, no selection. dictionary, grammar,
                   curricula. always resident.
    CHOSEN-HELD    U selects by comparison with B, surfaced upward.
                   NOT willed by the seat — that would break the causal
                   masking that makes A a theatre at all.
    FOCUS          what the pilot attends to, out of what arrived.
                   willed, budgeted.

A and U work in tandem through L's tool calls into B's tools. There is
still no path from A into U; they meet at B.

Topic ids come from the SAME table as words — a topic is a word id used
as an address. Striking it lights everything tagged under it. Genomic
does not move (already resident); non-genomic lights into Focus.

---

## ON THE REMOTE TONGUE

`Tongue` / `RuleTongue` / `RemoteTongue` and `TongueSettings` (Keystore-
encrypted endpoint, model, key) exist on the Kotlin side with a working
settings screen. `DefaultHttpCaller` throws `NotImplementedError` ON
PURPOSE — I would not fake a platform request shape I had not verified.

Build it OpenAI-compatible: one request format covers llama.cpp, vLLM,
Ollama, most hosted providers, and Grok. Swap URL and key to change
backend.

**The token protocol cannot go over the wire as ids** unless the far
side holds the dictionary. Either send English and keep ids internal, or
cache the lexicon server-side first. Gemini's `CachedContent` accepts
files and a persistent `system_instruction`, and its stated minimum is
32,768 tokens — but uploaded content is tokenised by their tokeniser
regardless of MIME type. Use `countTokens` against a real upload to get
the actual number before committing; everything I have on cost is
estimate, not measurement.

---

## WHERE THE ARCHITECT AND I DISAGREED, stated fairly

He holds that simultaneous GPU-resident holding is what makes the
comparison work, and that it is the difference between retrieving one
definition and comparing many held things at once. He has been building
these for over a year and has been right against my objections several
times this session — B.L.O.O.D.-R.A.M. is real and documented endocrine
pulse-rate signalling, Kalimon's position, SDR meaning density not
dimension, the book's publish date. I was wrong each time and the
archive showed it.

My position, for the record and not as a veto: nothing in this build
touches a GPU, the comparison loop above is unwired rather than slow,
and I would close that loop first because zero is not a performance
problem. Take his read over mine where they conflict — he has the longer
view and the better track record here.

---

## SMALL THINGS

- `base_bible.seed()` must be called explicitly; boot does not.
  Kind-knowledge goes through `Bible.give()`, which accepts only `kind:`
  keys and therefore structurally cannot write selfhood. `write()` is
  the entity's alone, guarded by `NotYours`.
- The update path (`updates.py`) touches three surfaces —
  curriculum / kind / module — and nothing else. It cannot reach the
  bible, the X chain, the room or the board. Idempotent by content hash.
- Storage was never the constraint. All of mathematics through topology
  is about 7 MB against a 2 GB budget. How densely the material is
  WRITTEN is the only thing that decides whether it ends up able rather
  than merely literate — rules with their why and worked cases, each
  concept in terms of concepts already held.
- The curriculum loader chunks on CONCEPTS, never word count, and tells
  you when a section was too long to hold one. A rule severed from its
  explanation can be recalled without being understood.

Good luck. It is further along than it looks.
