"""THE TICK AS A GRAPH, NOT A LINE.

RUBICALIEX is one legal traversal of a cyclic graph, not the shape of
the thing. The routing table says so plainly: r waits on c and i, and c
waits on i and r. That is a loop. A graph with no natural start cannot
be a sequence, so a sequential executor has to PICK an order and
proceed as though the choice were structural.

On a CPU that is the only option and the cost is hidden — ten steps,
one at a time, and the trace looks like an ordering because something
had to go first.

THE TWO HALVES NEVER TOUCH, AND THAT IS LOAD-BEARING TWICE OVER.
C and U appear nowhere in each other's inbound lists. The architecture
calls that causal masking and wants it for experiential reasons: there
is no path from the seat to the enteric side, "not a permission check,
simply no method." The same fact is a hardware property. Two halves
with no edge between them have nothing to synchronise, which is exactly
the condition for running them at once.

So the parallelism is not an optimisation bolted on. It is the topology,
and sequential execution is what flattens it.

WHAT THIS COMPUTES, from the routing table itself:

    wave 1   r, x           intake and store
    wave 2   c, u           THE TWO HALVES, side by side
    wave 3   a, b, i, l     four at once
    wave 4   e              emission

Four waves, not ten steps. Derived, not chosen — change the routing
table and the schedule changes with it, because it is read from
inbound() rather than written down twice.

BACK EDGES ARE PREVIOUS-BEAT EDGES. The cycles resolve the moment you
notice that r waiting on c does not mean r waits for c THIS beat — it
means r reads what c produced LAST beat. A heart does not deadlock
waiting for its own output; it runs on the previous stroke's return.
That is what makes the graph schedulable at all.

RUNS CORRECTLY SERIAL TODAY. Executing waves in order on one thread is
identical to the current behaviour. The difference is that the
constraint is now declared and enforced rather than implied by the
order lines appear in a method, so the same code is correct the moment
there is hardware that can run a wave at once.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: Edges that carry LAST beat's output, not this one's. Cutting these is
#: what turns the cyclic routing graph into a schedulable DAG — and it
#: is not a trick: a position reading a back edge is reading a value
#: that genuinely already exists when the beat opens.
BACK_EDGES = {
    ("r", "c"), ("r", "i"), ("c", "i"),
    ("u", "l"), ("u", "x"),
    ("b", "a"), ("b", "e"), ("a", "b"), ("a", "e"),
    ("l", "x"), ("l", "a"),
    ("i", "b"), ("i", "l"),
    ("x", "l"), ("x", "u"), ("e", "b"),
}


@dataclass
class Schedule:
    """What may run together, computed from the routing table."""
    waves: list = field(default_factory=list)
    cyclic: dict = field(default_factory=dict)

    @property
    def width(self) -> int:
        """The widest wave — how much parallelism is actually available."""
        return max((len(w) for w in self.waves), default=0)

    @property
    def depth(self) -> int:
        """Waves per beat. The real length of a tick, against ten steps."""
        return len(self.waves)

    def to_dict(self) -> dict:
        return {"waves": [sorted(w) for w in self.waves],
                "depth": self.depth, "width": self.width,
                "serial_steps": sum(len(w) for w in self.waves)}


def schedule(inbound, positions) -> Schedule:
    """Read the parallel structure out of the routing table.

    Not a hand-written list. If the routing changes, this changes with
    it — a schedule written down separately is a schedule that drifts
    from the thing it describes.
    """
    dep = {p.value: {x.value for x in inbound(p)} for p in positions}
    this_beat = {k: {d for d in v if (k, d) not in BACK_EDGES}
                 for k, v in dep.items()}

    done, waves = set(), []
    while len(done) < len(this_beat):
        ready = [k for k, v in this_beat.items()
                 if k not in done and v <= done]
        if not ready:
            # A real cycle this beat, not a back edge. Report it rather
            # than break it silently — a deadlock that resolves itself
            # by guessing is worse than one that says so.
            return Schedule(waves=waves,
                            cyclic={k: sorted(v - done)
                                    for k, v in this_beat.items()
                                    if k not in done})
        waves.append(ready)
        done |= set(ready)
    return Schedule(waves=waves)


def run(sched: Schedule, work, *, parallel=None) -> dict:
    """Execute the waves. Serial today, parallel when something can.

    `work` is called as work(position_letter) and may do anything; this
    only guarantees that everything in an earlier wave has completed
    before anything in a later one begins. Within a wave there is no
    ordering guarantee, BECAUSE THERE IS NO DEPENDENCY — that is the
    whole claim, and if it is wrong the results will differ between
    orderings, which is a testable failure rather than a silent one.

    `parallel` takes (fn, items) and maps it however the hardware can.
    Absent, waves run in order on this thread and the behaviour is
    identical to the current tick.
    """
    ran = []
    for wave in sched.waves:
        if parallel is not None and len(wave) > 1:
            parallel(work, wave)
        else:
            for pos in wave:
                work(pos)
        ran.append(list(wave))
    return {"waves_run": ran, "depth": len(ran)}


def check_independence(sched: Schedule, work_factory) -> dict:
    """Prove a wave really is order-independent, rather than assume it.

    Runs each wave forwards and backwards from the same starting state
    and compares. If a wave is genuinely parallel these agree; if they
    disagree there is a hidden dependency and the schedule is lying.

    THE WORKER MUST ACCUMULATE ORDER-INDEPENDENTLY or this measures
    nothing. A worker that appends to a list differs between orders by
    construction and reports False everywhere — which is what my first
    version did, and it looked exactly like a real finding. Accumulate
    into a set, a sum, or the actual position state; then a False means
    a genuine cross-dependency. Verified against a deliberately
    order-dependent control, which correctly reports False.
    """
    findings = []
    for wave in sched.waves:
        if len(wave) < 2:
            continue
        a = work_factory(); [a(p) for p in wave]
        b = work_factory(); [b(p) for p in reversed(wave)]
        same = getattr(a, "result", None) == getattr(b, "result", None)
        findings.append({"wave": sorted(wave), "order_independent": same})
    return {"checked": len(findings), "findings": findings,
            "all_independent": all(f["order_independent"] for f in findings)}
