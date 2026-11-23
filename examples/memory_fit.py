"""Model fit against memory the system reports at runtime.

Budget = weights + cache + scratch, compared against reported memory after a system
reserve and an inference overhead. The verdict is a state, not a boolean, because
"fits" without an environment record is not a compatibility claim.

Standalone, standard library only. Run: python3 memory_fit.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

GIB = 2**30


class Verdict(str, Enum):
    TESTED = "tested"
    NOT_VALIDATED = "not validated"
    INCOMPATIBLE = "incompatible"


@dataclass(frozen=True)
class ModelSpec:
    name: str
    total_params_b: float  # resident parameters, not active ones
    bits_per_weight: float
    layers: int
    kv_heads: int
    head_dim: int
    kv_bytes: float = 2.0


@dataclass(frozen=True)
class MemoryReport:
    """What the operating system reports, never what a product page states."""

    reported_gib: float
    system_reserve: float = 0.22
    overhead: float = 0.12


def weight_gib(spec: ModelSpec) -> float:
    return spec.total_params_b * 1e9 * spec.bits_per_weight / 8 / GIB


def cache_gib(spec: ModelSpec, context_tokens: int, batch: int = 1) -> float:
    per_token = 2 * spec.layers * spec.kv_heads * spec.head_dim * spec.kv_bytes
    return batch * context_tokens * per_token / GIB


def plan(spec: ModelSpec, memory: MemoryReport, context_tokens: int) -> tuple[Verdict, dict[str, float]]:
    budget = memory.reported_gib * (1 - memory.system_reserve) * (1 - memory.overhead)
    weights = weight_gib(spec)
    cache = cache_gib(spec, context_tokens)
    scratch = 0.05 * (weights + cache)
    need = weights + cache + scratch
    verdict = Verdict.NOT_VALIDATED if need <= budget else Verdict.INCOMPATIBLE
    numbers = {"budget": budget, "weights": weights, "cache": cache, "need": need,
               "margin": budget - need}
    return verdict, numbers


def show(spec: ModelSpec, memory: MemoryReport, context_tokens: int) -> None:
    verdict, n = plan(spec, memory, context_tokens)
    print(f"{spec.name} | reported {memory.reported_gib:.0f} GiB | context {context_tokens:,}")
    print(f"  weights {n['weights']:.2f}  cache {n['cache']:.2f}  need {n['need']:.2f} GiB")
    print(f"  budget {n['budget']:.2f} GiB, margin {n['margin']:+.2f} GiB, verdict: {verdict.value}")


def main() -> int:
    spec = ModelSpec(name="example-30b-a3b", total_params_b=30.0, bits_per_weight=4.25,
                     layers=48, kv_heads=8, head_dim=128)
    # Same model, same machine, two context lengths: the cache decides.
    for context_tokens in (32_768, 262_144):
        show(spec, MemoryReport(reported_gib=96), context_tokens)
    # Reported memory, not the nominal specification, sets the budget.
    show(spec, MemoryReport(reported_gib=32), 4_096)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
