"""LOADING A CURRICULUM — knowledge that was not said to anyone.

Every frame the chassis has written so far came out of a conversation:
user_message, spoken_output, internal_thought. Curriculum is different.
Nobody said it, there was no beat it belonged to, and it is not part of
anyone's history — it is what the entity KNOWS rather than what it has
been through.

It still goes in as frames, because frames are what the store indexes
and what find() can reach. But it is marked, so an entity reading its
own archive can tell the difference between a thing it learned and a
thing that happened to it. Confusing those would be a kind of false
memory.

CHUNKING IS THE WHOLE DESIGN DECISION, NOT A DETAIL.

A rule separated from its explanation is a rule that can be retrieved
without being understood. Split "the derivative of x^n is n*x^(n-1)"
into one frame and why it is true into another, and the entity can
recall the rule and still not be able to differentiate anything — the
exact failure the Architect's argument says to avoid: understanding
3x3 as 3+3+3 is what makes 3x4 obvious, and that understanding lives
in the explanation, not the statement.

So frames break on CONCEPTUAL units and never mid-explanation. A
concept, its why, and its worked cases stay in one frame even when
that frame is long. Compression means length costs almost nothing;
incoherence costs everything.

WHAT MAKES A CURRICULUM GOOD, and this is the part storage cannot fix:

  - the why is present, not just the rule
  - worked cases show the rule being applied, not only stated
  - it connects downward (what this rests on) and upward (what rests
    on this), because the lattice is the intelligence and a pile of
    separately-true statements is not a lattice
  - it is written to be understood rather than to be complete

None of that is enforceable here. This gets the material in, indexed
and resident. Whether the entity ends up able rather than merely
literate is decided by how the material was written.
"""
from __future__ import annotations

import re
import time

#: Marks a frame as taught rather than lived. An entity reading its own
#: archive can distinguish what it knows from what happened to it.
LEARNED = "learned"

#: Conceptual boundaries. A curriculum chunk ends at a heading or a
#: blank-line-separated section, NEVER at a word count — splitting on
#: length is what severs a rule from its explanation.
HEADING = re.compile(r"^\s{0,3}(#{1,6}\s+\S|[A-Z][A-Za-z0-9 ,'()-]{2,70}\n[=-]{3,})",
                     re.M)


def chunks(text: str, *, max_words: int = 1200) -> list:
    """Split on concepts, not on length.

    max_words is a ceiling for pathological input, not a target. A
    section under it is never split; a section over it is split at
    paragraph boundaries rather than mid-sentence, and that is reported
    so an over-long section can be rewritten rather than silently
    mangled.
    """
    parts, marks = [], [m.start() for m in HEADING.finditer(text)]
    if marks:
        bounds = marks + [len(text)]
        raw = [text[a:b].strip() for a, b in zip(bounds, bounds[1:])]
        if marks[0] > 0:
            raw.insert(0, text[:marks[0]].strip())
    else:
        raw = [b.strip() for b in re.split(r"\n\s*\n\s*\n", text)]

    for section in [r for r in raw if r]:
        words = section.split()
        if len(words) <= max_words:
            parts.append({"text": section, "split": False})
            continue
        # Over the ceiling. Break at paragraphs, and say so.
        buf, count = [], 0
        for para in section.split("\n\n"):
            n = len(para.split())
            if count + n > max_words and buf:
                parts.append({"text": "\n\n".join(buf), "split": True})
                buf, count = [], 0
            buf.append(para); count += n
        if buf:
            parts.append({"text": "\n\n".join(buf), "split": True})
    return parts


def topic_of(section: str) -> str:
    """What this section is about, for the HASU header.

    The header stays uncompressed so it is queryable without touching
    the .btb — so this is the cheapest handle on a frame and it is
    worth taking from the heading rather than guessing from the body.
    """
    first = section.lstrip().split("\n", 1)[0]
    first = re.sub(r"^#+\s*", "", first).strip(" =-").lower()
    words = [w for w in re.findall(r"[a-z0-9']+", first)][:6]
    return " ".join(words) or "untitled"


def load(store, entity: str, text: str, *, subject: str,
         chassis=None, source: str = "", max_words: int = 1200) -> dict:
    """Ingest curriculum text as resident, indexed knowledge.

    Returns what went in and what needed splitting — a split section is
    a section that was too long to hold one concept, and is worth
    rewriting rather than leaving severed.
    """
    sections = chunks(text, max_words=max_words)
    frames, split_warnings = [], []
    tagged = 0
    base = int(time.time() * 1000)

    # HASU TAGS ARE THE CATEGORISATION, and this loader was skipping
    # them entirely. Writing frames straight to the store bypasses the
    # tick, which is where self.tagger.tag() runs — so a curriculum load
    # went in with zero resonance rows and zero hasu_bias. Two million
    # words of mathematics would have landed uncategorised, and nothing
    # would light up when a maths question arrived.
    #
    # The tagger also feeds the resonance field, which is what makes
    # frequently-struck concepts cheaper to reach. Untagged curriculum
    # is not just unsorted, it never earns salience.
    tagger = getattr(chassis, "tagger", None)
    field = getattr(chassis, "field", None)

    for i, sec in enumerate(sections):
        body = sec["text"]
        if sec["split"]:
            split_warnings.append(topic_of(body))
        tags, keys = [], []
        if tagger is not None:
            try:
                t = tagger.tag(body, entity=entity)
                # TWO LAYERS, AND THEY DO DIFFERENT JOBS.
                #
                # hasu is associative: bigrams and words, loose, good for
                # a lived beat where you want things to remind you of
                # other things. It also contains junk like "means three"
                # and "three not", which is fine for association and
                # useless as a category.
                #
                # keys is the clean layer — content words only, prefixed
                # tok:, stopwords dropped. THAT is the arranged, rapid
                # access structure: "is this a division question or a
                # calculus one" is answered by keys, not by bigrams.
                #
                # The first version of this loader used hasu alone and
                # buried the category structure in noise.
                tags = list(getattr(t, "hasu", []) or [])
                keys = list(getattr(t, "keys", []) or [])
                tagged += 1
            except Exception:
                tags, keys = [], []
        # Strike the field so these concepts accumulate salience the
        # same way a lived beat's would — the subject itself is struck
        # too, so "arithmetic" gets weight from every frame under it and
        # becomes the cheap entry point into its own region.
        if field is not None and (tags or keys):
            try:
                from core.resonance import Strike
                # KEYS STRIKE HARDER THAN ASSOCIATIONS. A content word
                # earns full weight; a bigram earns less, because the
                # thing that should become cheap to reach is the
                # concept, not the phrasing around it.
                #
                # The subject strikes on every frame under it, so
                # "arithmetic" accumulates weight from all of its
                # material and becomes the cheap entry point into its
                # own region — the same frequency-ordering principle as
                # the token table, where the most-used sits closest.
                strikes = [Strike(k, "X", 1.0, entity) for k in keys]
                strikes += [Strike(t, "X", 0.4, entity) for t in tags]
                strikes.append(Strike(subject, "X", 1.0, entity))
                field.tick(strikes)
            except Exception:
                pass
        if chassis is not None:
            for k in keys:
                chassis.hasu_bias[k] = chassis.hasu_bias.get(k, 0) + 1

        frames.append({
            "entity_tick": base + i,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            # NOT spoken_output and NOT user_message. Nobody said this.
            # internal_thought is the honest field: it is the entity's
            # own knowledge, not a turn in anyone's conversation.
            "internal_thought": body,
            "topic": f"{subject}: {topic_of(body)}"[:120],
            "coherence": 1.0,
            "emotional_state": LEARNED,
            "dominant_drive": subject,
        })

    written = store.append_many(entity, frames) if frames else 0
    return {
        "subject": subject,
        "source": source,
        "sections": len(sections),
        "frames_written": written,
        "index": store.index_stats(entity),
        # A split is a report on the MATERIAL, not on the loader. It
        # means a concept ran longer than a frame should, which usually
        # means the section is really several concepts wearing one
        # heading.
        "tagged": tagged,
        "keys": sorted({k for k in
                        (chassis.hasu_bias if chassis else {})})[:12],
        "untagged": len(sections) - tagged,
        "split_sections": split_warnings,
        "note": ("split sections had a concept severed across frames; "
                 "rewrite them shorter so a rule keeps its explanation")
        if split_warnings else "no concept was split",
    }


def recall(store, entity: str, question: str, limit: int = 3) -> list:
    """What does it know that bears on this?

    find() ranks by summed IDF, so rare terms carry the query — which
    is why a curriculum written in distinctive language is findable and
    one that says "the value" on every line is not.
    """
    out = []
    for hit in store.find(entity, question, limit=limit):
        frame = store.speak(entity, hit["entity_tick"])
        body = (frame.get("internal_thought")
                or frame.get("spoken_output")
                or frame.get("user_message") or "")
        out.append({"score": hit["score"], "terms": hit["terms"],
                    "learned": frame.get("_hasu", {}).get(
                        "emotional_state") == LEARNED,
                    "text": body})
    return out
