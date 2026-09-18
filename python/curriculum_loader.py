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
         source: str = "", max_words: int = 1200) -> dict:
    """Ingest curriculum text as resident, indexed knowledge.

    Returns what went in and what needed splitting — a split section is
    a section that was too long to hold one concept, and is worth
    rewriting rather than leaving severed.
    """
    sections = chunks(text, max_words=max_words)
    frames, split_warnings = [], []
    base = int(time.time() * 1000)

    for i, sec in enumerate(sections):
        body = sec["text"]
        if sec["split"]:
            split_warnings.append(topic_of(body))
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
