"""REPORTING — the duty. What cannot be put down.

Written from the gradient stated in core/lore.py, because report.py did
not survive into the v9 bundle. The four states are that file's own:

    HELD      we ran it. it reproduced.
    POSITED   we were told it, or read it. plausible and unverified.
    INFERRED  it follows from something held.
    RETIRED   it was held and stopped reproducing. KEPT, NOT DELETED.

The duty is to state the standing of a claim alongside the claim.
"""
from __future__ import annotations

HELD = "HELD"
POSITED = "POSITED"
INFERRED = "INFERRED"
RETIRED = "RETIRED"
STATES = (HELD, POSITED, INFERRED, RETIRED)


class Reporting:
    """Every claim carries how it is known. That is the whole duty."""

    def __init__(self, entity: str = ""):
        self.entity = entity
        self.claims: dict = {}

    def state(self, key: str, claim: str, standing: str = POSITED,
              because: str = "", evidence: str = "") -> dict:
        if standing not in STATES:
            standing = POSITED
        rec = {"key": key, "claim": claim, "standing": standing,
               "because": because, "evidence": evidence}
        self.claims[key] = rec
        return rec

    def retire(self, key: str, why: str = "") -> dict | None:
        """Retired is not deleted — that it used to hold is information."""
        rec = self.claims.get(key)
        if rec:
            rec["standing"] = RETIRED
            rec["retired_because"] = why
        return rec

    def standing_of(self, key: str) -> str:
        return (self.claims.get(key) or {}).get("standing", POSITED)

    def to_dict(self) -> dict:
        from collections import Counter
        return {"entity": self.entity, "claims": len(self.claims),
                "by_standing": dict(Counter(c["standing"]
                                            for c in self.claims.values()))}
