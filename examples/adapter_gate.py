"""Promotion and rollback state machine for a learned adapter.

A candidate is scored against the active version on a frozen evaluation set. Promotion
needs a gain above a margin and no regression beyond tolerance. The previous version
stays loadable, so rollback is a pointer change and not a restore.
Standalone, standard library only. Run: python3 adapter_gate.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled back"


@dataclass(frozen=True)
class Score:
    quality: float  # mean score on the frozen set, higher is better
    regression: float  # share of probe cases that got worse, lower is better


@dataclass
class Version:
    label: str
    score: Score
    state: State = State.CANDIDATE


@dataclass
class Gate:
    min_gain: float = 0.03
    max_regression: float = 0.02
    active: Version | None = None
    previous: Version | None = None
    audit: list[str] = field(default_factory=list)

    def adopt(self, version: Version) -> None:
        version.state = State.PROMOTED
        self.active = version
        self.audit.append(f"adopted {version.label}")

    def decide(self, candidate: Version) -> Version:
        if self.active is None:
            raise RuntimeError("adopt a baseline before evaluating a candidate")
        gain = candidate.score.quality - self.active.score.quality
        worse = candidate.score.regression
        if gain >= self.min_gain and worse <= self.max_regression:
            candidate.state = State.PROMOTED
            self.previous, self.active = self.active, candidate
        else:
            candidate.state = State.REJECTED
        self.audit.append(f"{candidate.state.value} {candidate.label}: "
                          f"gain {gain:+.3f}, regression {worse:.3f}")
        return candidate

    def rollback(self) -> Version:
        if self.previous is None:
            raise RuntimeError("nothing to roll back to")
        self.active.state = State.ROLLED_BACK
        self.previous, self.active = self.active, self.previous
        self.active.state = State.PROMOTED
        self.audit.append(f"rolled back to {self.active.label}")
        return self.active


def main() -> int:
    gate = Gate()
    gate.adopt(Version("adapter-v1", Score(quality=0.700, regression=0.0)))
    for candidate in (
        Version("adapter-v2", Score(quality=0.745, regression=0.010)),
        Version("adapter-v3", Score(quality=0.790, regression=0.060)),
        Version("adapter-v4", Score(quality=0.702, regression=0.000)),
    ):
        gate.decide(candidate)
        print(f"active after {candidate.label}: {gate.active.label} ({candidate.state.value})")
    print("after rollback:", gate.rollback().label)
    print("\naudit trail:")
    for entry in gate.audit:
        print(" -", entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
