# Toy-model comprehension test

Does a ~30M-parameter model (TinyStories-33M) hold the SHAPE of our
comprehension curriculum when it's handed as context, or does it just
produce fluent word-salad that ignores what was actually asked?

Real test, not a foregone conclusion. If yes: the smallest possible
tongue is enough, and capability comes from held knowledge, not model
size — the thesis this whole build rests on. If no: toy scale can't
hold a procedure, and SmolLM2-135M (or larger) is the real floor.

## Run it

    pip install transformers torch
    python test_toy_model.py

Free-tier Colab GPU is enough. CPU works too but is a weaker test —
the architecture's own claim is that this needs real simultaneity,
which a GPU gives and a slow CPU forward-pass may not fairly represent.
A negative CPU result is suggestive, not final.

## What to look at

Three questions, each testing a different comprehension shape:
- "What is a keystone?" — definitional
- "Why does an arch stand up?" — should recognize CAUSE is wanted
- "How are you?" — should recognize STATE/MANNER is wanted, not
  define the word "how"

Judge each answer against its expected shape, printed alongside it.
