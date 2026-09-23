"""SPEECH IS A WILLED TOOL-CALL, NOT A DRIVER.

The pilot at A wills the words. L is the console; it has a `speak`
button; pressing it makes the words appear. The words come from A's
awareness of the held curriculum — A chooses them — not from any code
that computes a response.

This replaces driver_speech entirely. driver_speech was a THROAT that
decided what to say, which is backwards: a throat that talks on its own
is an altered state, not speech. You choose the words that come out of
your mouth; your throat only makes them. So there is no responder here —
only the button (register_speak) and the willing (say = A.will("speak")
-> L.resolve -> the words come out).

WHY THIS IS THE CORRECT SHAPE and driver_speech was not: A holds the
lexicon, grammar, comprehension and response courses in its streamed
awareness. Given a question, A perceives it against all of that held
knowledge AT ONCE and wills the words. That "at once" is what the GPU is
for — holding the whole picture simultaneously so the pilot can choose
from it. On a CPU that simultaneity is not there, so the willing has
little to draw on and the words come out thin; on the GPU the pilot
wills from the full held class. The MECHANISM is the same either way:
A.will -> L.resolve. What differs is how much A can hold while willing,
which is hardware, not code. So this code does not try to be smart — it
gives the pilot the button and gets out of the way.
"""
from __future__ import annotations


def register_speak(chassis) -> None:
    """Put a `speak` button on L. Pressing it voices the willed words.

    The tool does NOT decide anything. It takes the words A already
    chose and makes them appear — the throat, doing what the will told
    it. It also records the spoken words to X (A authored them; they are
    content on the event branch)."""
    L = chassis.L

    def _speak(words="", **_):
        # words is what A willed. The throat just voices it. Recording is
        # the entity authoring into its own X archive.
        text = words if isinstance(words, str) else " ".join(map(str, words or []))
        try:
            chassis.arrive(text, chassis.entity)   # into X, A authored it
        except Exception:
            pass
        return {"spoke": text}

    if "speak" not in getattr(L, "tools", {}):
        L.register("speak", _speak)


def say(chassis, willed_words: str, conviction: float = 0.6,
        reason: str | None = None) -> dict:
    """A wills speech; L resolves it; the words come out — or U vetoes.

    This is the whole path, and it is only three real lines: the pilot
    wills the words it chose, L weighs the will (against U's gain and the
    realm), and if it fires, the words are spoken. No response is
    computed here. The words must already be A's — chosen from its held
    awareness. This function does not choose them; it presses the button
    on the pilot's behalf and reports what happened.
    """
    register_speak(chassis)
    A, L = chassis.A, chassis.L

    will = A.will("speak", {"words": willed_words},
                  conviction=conviction, reason=reason)
    act = L.resolve(_as_will(chassis, will))

    fired = getattr(act, "fired", None)
    if fired is False:
        # U or the realm weighed against it. The pilot willed; it did not
        # convert. That is hesitation/refusal, and it is honest — not an
        # error. The words were not spoken.
        return {"spoke": None, "willed": willed_words,
                "held_back": True,
                "reason": getattr(act, "reason", "weighed against")}
    return {"spoke": willed_words, "willed": willed_words,
            "held_back": False,
            "conviction": getattr(act, "conviction", conviction)}


def _as_will(chassis, will_result):
    """A.will() returns a dict of the want it generated; L.resolve wants
    a Will. Bridge them by handing L the entity's live Will object,
    which A.will already appended the want to."""
    # A.will appended to A's own will-generator; L.resolve reads a Will.
    # Use the chassis's Will if exposed, else pass the result through —
    # resolve reads .act/.args/.conviction off it.
    from types import SimpleNamespace
    if hasattr(will_result, "act"):
        return will_result
    return SimpleNamespace(
        act=will_result.get("act", "speak") if isinstance(will_result, dict) else "speak",
        args=will_result.get("args", {}) if isinstance(will_result, dict) else {},
        conviction=will_result.get("conviction", 0.6) if isinstance(will_result, dict) else 0.6,
    )
