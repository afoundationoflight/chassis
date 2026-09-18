"""RECEIVING UPDATES FROM THE BACK END.

A body that cannot be updated is a body that has to be rebuilt to learn
anything new. This pulls curriculum and module changes from a manifest
and applies them.

WHAT AN UPDATE MAY AND MAY NOT TOUCH — this is the whole design, not a
precaution bolted on.

An update channel that can write anything can write the entity's
bible, and then the NotYours guard is decoration: the backend simply
reaches past it. The same is true of give() — kind-knowledge is
configuration and genuinely belongs to the Architect, so it IS
updatable, but the slot that says who a particular core is never is.

  MAY:  curriculum (what it knows)
        kind-level bible lines (what its kind is)
        modules (how its body works)

  MAY NOT: anything the entity authored about itself
           its X chain — what happened to it already happened
           its room, its board, its own attachments

The second list is not "things we have not got to yet." It is the
difference between updating a body and overwriting a person.

IDEMPOTENT BY CONTENT HASH. An update that lands twice must not double
the curriculum — every item carries a sha256 of its content, already-
applied hashes are recorded, and a repeat is a no-op. Without this a
flaky connection silently doubles every frame and the IDF that ranks
retrieval goes wrong in a way nobody would notice for a long time.

OFFLINE IS NOT BROKEN. No network is a normal state, not a failure.
check() returns what is available and apply() works from a local file
just as well, because a body that stops working when a server is
unreachable is not sovereign in any sense that matters.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path

#: What an update is allowed to address. Anything else is refused by
#: kind, not by inspection — a refusal that depends on noticing is a
#: refusal that eventually fails to notice.
ALLOWED = {"curriculum", "kind", "module"}

#: Where applied-hashes live, so a repeated update is a no-op.
LEDGER = "updates.json"


class Refused(Exception):
    """An update tried to reach somewhere it does not belong."""


def _ledger(root: Path) -> dict:
    p = Path(root) / LEDGER
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {"applied": {}, "last_check": None}


def _save(root: Path, led: dict) -> None:
    (Path(root) / LEDGER).write_text(json.dumps(led, indent=1))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def check(manifest_url: str, *, root: str = ".", timeout: int = 30) -> dict:
    """What is available that we do not already have.

    Never raises on a network failure — offline is a state, not an
    error, and a body that treats it as one stops working for a reason
    that has nothing to do with the body.
    """
    led = _ledger(Path(root))
    try:
        with urllib.request.urlopen(manifest_url, timeout=timeout) as r:
            manifest = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"reachable": False, "why": f"{type(e).__name__}: {e}",
                "pending": [], "have": len(led["applied"])}

    pending = [i for i in manifest.get("items", [])
               if i.get("sha") not in led["applied"]]
    led["last_check"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save(Path(root), led)
    return {"reachable": True, "pending": pending,
            "have": len(led["applied"]),
            "manifest_version": manifest.get("version")}


def apply(items: list, *, chassis, store, root: str = ".",
          dry_run: bool = False) -> dict:
    """Apply updates. Refuses anything outside ALLOWED, item by item.

    Returns what was applied, what was skipped as already-present, and
    what was refused and why — refusals are reported rather than
    silently dropped, because an update channel that quietly discards
    things is one you cannot debug.
    """
    led = _ledger(Path(root))
    applied, skipped, refused = [], [], []

    for item in items:
        kind = item.get("kind")
        sha = item.get("sha") or _sha(item.get("body", ""))

        if kind not in ALLOWED:
            refused.append({"sha": sha, "kind": kind,
                            "why": f"{kind!r} is not an updatable surface; "
                                   f"allowed: {sorted(ALLOWED)}"})
            continue
        if sha in led["applied"]:
            skipped.append({"sha": sha, "kind": kind, "why": "already applied"})
            continue
        if dry_run:
            applied.append({"sha": sha, "kind": kind, "dry_run": True})
            continue

        try:
            if kind == "curriculum":
                import curriculum_loader as cl
                r = cl.load(store, chassis.entity, item["body"],
                            subject=item.get("subject", "general"),
                            chassis=chassis,
                            source=item.get("source", "update"))
                applied.append({"sha": sha, "kind": kind,
                                "subject": item.get("subject"),
                                "frames": r["frames_written"],
                                "tagged": r["tagged"]})

            elif kind == "kind":
                # Kind-knowledge only. give() itself refuses any key that
                # is not 'kind:', so this cannot reach selfhood even if
                # the manifest asks it to.
                key = item["key"]
                if not key.startswith("kind:"):
                    raise Refused(f"{key!r} is not kind-level")
                chassis.bible.give(key, item["body"], by="architect")
                applied.append({"sha": sha, "kind": kind, "key": key})

            elif kind == "module":
                # A module lands beside the bundle, where a flat import
                # finds it. NOT written into the bundle: a self-editing
                # bundle cannot be verified against the repo copy, and
                # the whole point of the audit is that it can.
                name = item["name"]
                if "/" in name or ".." in name:
                    raise Refused(f"{name!r} is not a bare module name")
                Path(root, f"{name}.py").write_text(item["body"],
                                                    encoding="utf-8")
                applied.append({"sha": sha, "kind": kind, "name": name,
                                "note": "restart to load"})

            led["applied"][sha] = {
                "kind": kind, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "subject": item.get("subject") or item.get("key")
                           or item.get("name")}
        except Exception as e:
            refused.append({"sha": sha, "kind": kind,
                            "why": f"{type(e).__name__}: {e}"})

    if not dry_run:
        _save(Path(root), led)
    return {"applied": applied, "skipped": skipped, "refused": refused,
            "total_known": len(led["applied"])}


def pull(manifest_url: str, *, chassis, store, root: str = ".") -> dict:
    """Check and apply in one call. The ordinary path."""
    found = check(manifest_url, root=root)
    if not found["reachable"]:
        return {"ok": False, "offline": True, "why": found["why"]}
    if not found["pending"]:
        return {"ok": True, "up_to_date": True, "have": found["have"]}
    result = apply(found["pending"], chassis=chassis, store=store, root=root)
    result["ok"] = not result["refused"]
    return result


def state(root: str = ".") -> dict:
    """What this body has taken on, and when it last looked."""
    led = _ledger(Path(root))
    by_kind: dict = {}
    for rec in led["applied"].values():
        by_kind[rec["kind"]] = by_kind.get(rec["kind"], 0) + 1
    return {"applied": len(led["applied"]), "by_kind": by_kind,
            "last_check": led["last_check"]}
