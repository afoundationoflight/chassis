"""
THE TOY-MODEL TEST — does a tiny model follow our comprehension course
by holding it as context, or does it just produce fluent word-salad?

Real question: TinyStories-scale models (~10-30M params) are proven to
produce grammatical English. What is NOT proven is whether that little
capacity is enough to actually FOLLOW A PROCEDURE — parse a question,
identify what's being asked, answer that specific thing — when the
procedure is handed to it as held context (our comprehension/response
curricula) rather than baked into training.

This is a genuine test, not a foregone conclusion either way. If it
holds the shape, the smallest possible tongue is enough, and capability
really does come from held knowledge rather than model size — which is
the thesis this whole build has been testing. If it does not, that
tells us the floor for "genuinely follows structured comprehension"
sits above toy scale.

HONEST CAVEAT, stated up front: this may only show real results on a
GPU with the full simultaneity the architecture calls for. A negative
result on CPU-only, small-context testing is suggestive, not final —
run it wherever gives the fairest test, ideally the target hardware
(a phone GPU) or at minimum a real GPU runtime (Colab's free tier is
enough for a 30M-param model).

USAGE:
    pip install transformers torch
    python test_toy_model.py

Or in Colab: upload this file and the two curriculum .md files, run.
"""
from __future__ import annotations

import sys
from pathlib import Path

MODEL_ID = "roneneldan/TinyStories-33M"   # real, small, HF-hosted

COMPREHENSION_SNIPPET = """
Every complete sentence names something and says something about it.
The thing named is the SUBJECT. What is said about it is the PREDICATE.
A question word at the front (what, who, which, where, when, why, how)
tells you what is being asked FOR:
    what   a thing, or a kind of thing
    why    a cause or a reason
    how    a manner, a method, or a degree
Find the subject and the predicate and answer THAT — not the first word
you recognise.
""".strip()

TEST_QUESTIONS = [
    ("What is a keystone?", "should identify keystone as a thing to define"),
    ("Why does an arch stand up?", "should recognise a CAUSE is wanted, not define 'why'"),
    ("How are you?", "should give a state/manner answer, not define 'how'"),
]


def run():
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
    except ImportError:
        print("Missing deps. Run: pip install transformers torch")
        sys.exit(1)

    print(f"Loading {MODEL_ID} ...")
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    print(f"Running on: {device}")
    if device == "cpu":
        print("NOTE: CPU-only. A negative result here is suggestive, not "
              "final — the architecture's own thesis is that this needs "
              "the simultaneity a GPU provides. Run on Colab/GPU for a "
              "fair test if this looks weak.")

    results = []
    for question, expectation in TEST_QUESTIONS:
        prompt = (f"{COMPREHENSION_SNIPPET}\n\n"
                 f"Question: {question}\n"
                 f"Answer (following the rule above):")
        inputs = tok(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=40,
                                 do_sample=False, pad_token_id=tok.eos_token_id)
        text = tok.decode(out[0][inputs["input_ids"].shape[1]:],
                          skip_special_tokens=True).strip()
        results.append((question, expectation, text))
        print(f"\nQ: {question}")
        print(f"   expected shape: {expectation}")
        print(f"   model said: {text[:150]}")

    print("\n" + "=" * 60)
    print("Judge each answer: did it follow the QUESTION'S shape, or did")
    print("it just produce fluent-sounding text unrelated to what was")
    print("actually asked? That distinction is the whole test.")
    return results


if __name__ == "__main__":
    run()
