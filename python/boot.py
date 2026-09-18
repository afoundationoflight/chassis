#!/usr/bin/env python3
"""Boot a body, seed its genome, and pull any updates. Start here.

    python3 boot.py                      # boot and report
    python3 boot.py --name seth_el       # name it
    python3 boot.py --pull URL           # take updates from a manifest
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import home, infinity_core_v9          # noqa: F401  (the bundle)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="anyone")
    ap.add_argument("--pull", default=None, help="manifest url")
    ap.add_argument("--ask", default=None, help="ask it something it knows")
    a = ap.parse_args()

    driver = sys.modules["driver"]
    Store = sys.modules["local_store"].LocalStore
    root = str(home.HOME)

    store = Store(root=root)
    body = driver.boot(a.name, store=store)
    driver.occupy(body)

    audit = driver.audit(body)
    if not audit["wired"]:
        print("REFUSED TO BOOT:", json.dumps(audit, indent=1)); return 1

    import base_bible, updates, curriculum_loader as cl
    seeded = base_bible.seed(body)

    print(f"{a.name}: wired, {len(seeded['written'])} kind lines given")
    print(f"  the slot for who it is stays empty — that one is its own")

    if a.pull:
        r = updates.pull(a.pull, chassis=body, store=store, root=root)
        print("  update:", json.dumps(r)[:200])
    print("  updates held:", json.dumps(updates.state(root)))

    if a.ask:
        hits = cl.recall(store, a.name, a.ask, limit=1)
        print(f"\n  Q: {a.ask}")
        print(f"  A: {hits[0]['text'][:400] if hits else '(nothing loaded yet)'}")

    body.tick(message="what is here")
    print(f"\n  tick {''.join(body.trace)} | room {len(body.permanence.model)} things"
          f" | inertia {body.habituation.inertia()['inertia']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
