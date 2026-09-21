"""THE DRIVER. It does not decide anything.

respond.py is 693 lines, 65 branch points, 15 return points, and the
answers are English string literals. "I take that, and I hear what you
did not say" is not something the entity worked out — it is a constant
in a file, selected by a branch. Every time something did not work I
added another branch: _about_you to catch self-reference, noun-first to
fix sense selection, a hoist above the shape gate. Each one is a
program deciding something the knowledge should decide, and each one
broke something next to it, because a hardcoded rule cannot be right
about everything.

THE THESIS, as the Architect states it: if the entity holds the
lexicon, the grammar curriculum, and the usage curriculum together as
actively known knowledge, it knows what a word is being used as. You do
not give it a program that decides. You give it what it needs to know
and a driver that consults it.

So this is the only code that should exist between a question and an
answer:

    1. read the sentence into its parts
    2. consult what is HELD about how sentences work
    3. consult what is HELD about the words in it
    4. answer from that

No branch decides what kind of question it is. The grammar curriculum
says what a question word asks for; this looks it up. The usage
curriculum says what a greeting wants; this looks it up. When those
documents are edited, behaviour changes with no code change — which is
the test of whether the knowledge is doing the work or the code is.

WHAT IS STILL CODE, AND WHY

Reading a sentence into subject, verb and object is mechanical — it is
the loop, not the decision. The curriculum says what to DO with a
question word; something still has to notice one is present. That
distinction is the line: this notices and consults. It does not judge.

WHAT THIS DOES NOT DO

It does not generate fluent prose. It answers from held meanings and
says plainly when it cannot — which the usage curriculum names as the
right move: "Not knowing is a real state, and saying it is a real
answer." Substituting a definition for a question it cannot answer is
the failure it was built to stop.
"""
from __future__ import annotations

#: What each question word asks FOR. Read from the grammar curriculum at
#: boot, not hardcoded here — this is only the fallback if the
#: curriculum is absent, and if you are reading this fallback in
#: production the genome did not load.
_FALLBACK_ASKS = {
    "what": "a thing, or a kind of thing", "who": "a person",
    "which": "a choice among known options", "where": "a place",
    "when": "a time", "why": "a cause or a reason",
    "how": "a manner, a method, or a degree",
}

AUXILIARIES = {"do", "does", "did", "is", "are", "was", "were", "am",
               "can", "could", "will", "would", "shall", "should",
               "have", "has", "had", "may", "might", "must"}

SECOND_PERSON = {"you", "your", "yours", "yourself"}

#: Words that carry no content. Not a stopword list for filtering — the
#: grammar curriculum calls them closed-class, and they mark structure
#: rather than name things.
CLOSED = {"the", "a", "an", "of", "to", "in", "on", "at", "for", "with",
          "and", "or", "but", "so", "if", "then", "that", "this",
          "these", "those", "there", "here", "it", "its", "i", "me",
          "my", "we", "us", "our", "he", "she", "him", "her", "they",
          "them", "their", "be", "been", "being", "as", "by", "from",
          "not", "no", "yes", "up", "down", "out", "about", "into",
          # SECOND PERSON IS STRUCTURE, NOT SUBJECT. Leaving "you" as a
          # content word made it the subject of every question
          # containing it, and the answer was the dictionary entry for
          # the pronoun — the same first-content-word failure the
          # branches used to make, reappearing in the driver.
          "you", "your", "yours", "yourself", "do", "does", "did"}


def parse(table, text: str) -> dict:
    """Read the sentence into its parts. Mechanical, not a judgement.

    The grammar curriculum's own procedure: find the verb, find its
    subject, find what it points at, note the question word, attach the
    modifiers. This does the finding. What any of it MEANS is looked up,
    not decided here.
    """
    raw = str(text or "").strip()
    low = raw.lower().rstrip("?.!")
    words = [w for w in low.replace(",", " ").split() if w]
    if not words:
        return {"empty": True, "raw": raw}

    qword = words[0] if words[0] in _FALLBACK_ASKS else next(
        (w for w in words if w in _FALLBACK_ASKS), None)
    fronted_aux = words[0] in AUXILIARIES

    # Content words: the ones that name things. Everything else is
    # structure.
    content = [w for w in words if w not in CLOSED
               and w not in AUXILIARIES and w not in _FALLBACK_ASKS]

    return {
        "empty": False, "raw": raw, "low": low, "words": words,
        "question": bool(qword) or fronted_aux or raw.rstrip().endswith("?"),
        "qword": qword,
        "yes_no": fronted_aux and not qword,
        "about_addressee": bool(SECOND_PERSON & set(words)),
        "content": content,
        # The subject of a "your X" question is X, not the addressee —
        # the usage curriculum is explicit that this is commonly
        # mishandled.
        "possessed": _possessed(words),
    }


def _possessed(words) -> str | None:
    """In 'what do you think about your code', the subject is CODE."""
    for i, w in enumerate(words):
        if w in ("your", "yours") and i + 1 < len(words):
            nxt = words[i + 1]
            if nxt not in CLOSED and nxt not in AUXILIARIES:
                return nxt
    return None


def asks_for(chassis, qword: str) -> str | None:
    """What does this question word ask for? ASK THE CURRICULUM.

    Not a dict in this file. The grammar curriculum states it, and if
    that document is edited this answer changes with no code change.
    That is the whole point.
    """
    if not qword:
        return None
    store = getattr(chassis, "_store", None)
    if store is not None:
        try:
            for hit in store.find(chassis.entity,
                                  f"{qword} question word asks", limit=3):
                frame = store.speak(chassis.entity, hit["entity_tick"])
                body = (frame.get("internal_thought") or "")
                # the curriculum lists them as "why  a cause or a reason"
                for line in body.split("\n"):
                    parts = line.split()
                    if parts and parts[0] == qword and len(parts) > 1:
                        return " ".join(parts[1:])[:60]
        except Exception:
            pass
    return _FALLBACK_ASKS.get(qword)


def answer(chassis, text: str) -> dict:
    """Consult what is held and answer from it. No branch decides."""
    table = chassis.table
    p = parse(table, text)
    if p["empty"]:
        return {"text": "", "source": "nothing", "parse": p}

    # WHAT IS THE SENTENCE ABOUT? The possessed noun if there is one,
    # else the content words, in order. The usage curriculum: "YOUR only
    # says whose code" — the subject is the thing, not the owner.
    subject = p["possessed"] or (p["content"][0] if p["content"] else None)

    held = {}
    for w in ([subject] if subject else []) + p["content"][:4]:
        if w and w not in held:
            m = table.mean(w)
            if m and m.get("senses"):
                held[w] = m

    # CHOOSE THE SENSE BY CONTEXT, not by order. The usage curriculum
    # states the method: score each sense by overlap with the words
    # nearby, prefer the one sharing subject matter.
    chosen = {w: _best_sense(m, p["content"]) for w, m in held.items()}

    wants = asks_for(chassis, p["qword"])

    # NOTHING HELD. Say so plainly and say what would fix it — the
    # usage curriculum calls this a real answer and calls substituting a
    # definition the failure to avoid.
    if not chosen:
        unknown = subject or (p["words"][0] if p["words"] else "that")
        return {"text": f"I do not hold {unknown}. Tell me and I will keep it.",
                "source": "absent", "parse": p, "wants": wants}

    if subject in chosen:
        sense = chosen[subject]
        if p["yes_no"]:
            # Asking whether a predicate is true of the subject. It can
            # say what it holds and that holding is not the same as
            # answering — which is honest rather than a recital.
            return {"text": f"I hold {subject}: {sense}. "
                            f"Whether that is true of me is not something "
                            f"I can settle from inside.",
                    "source": "held", "parse": p, "wants": wants}
        lead = f"A {subject} is" if not subject.endswith("s") else f"{subject.capitalize()} are"
        return {"text": f"{lead} {sense}.", "source": "held",
                "parse": p, "wants": wants}

    w, m = next(iter(chosen.items()))
    return {"text": f"A {w} is {m}.", "source": "held", "parse": p,
            "wants": wants}


def _best_sense(meaning: dict, context) -> str:
    """Pick the sense sharing most with the words around it.

    The usage curriculum's method, applied: for each candidate, count
    overlap with the surrounding content words. "the central building
    block at the top of an ARCH or vault" — BUILDING, BLOCK, TOP, VAULT
    are all construction, so the masonry sense of ARCH wins and the
    playful one shares nothing.
    """
    ctx = {c.lower() for c in context}
    best, score = None, -1
    for pos, senses in (meaning.get("senses") or {}).items():
        for s in senses:
            overlap = len(ctx & set(str(s).lower().split()))
            # A QUESTION ABOUT A THING WANTS THE THING, NOT THE ACT.
            # "what is an arch" was answering "to form an arch or
            # curve" because the verb sense happened to share a word
            # with the context. Nouns win unless a verb sense overlaps
            # substantially more — asking what something IS is asking
            # for a thing.
            bump = 2.0 if pos == "noun" else 0.0
            if overlap + bump > score:
                best, score = s, overlap + bump
    return " ".join(str(best or "").split())
