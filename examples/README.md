# Examples

Three small programs that demonstrate technique used in the architecture. They were written from
scratch for this repository, share no code with the private work, and contain no product data, model
names or vendor specifics.

Each file runs on its own with the Python standard library. Python 3.10 or later is required for the
union type syntax. There are no dependencies and no configuration.

```
python3 runtime_contract.py
python3 memory_fit.py
python3 adapter_gate.py
```

## runtime_contract.py

Defines an adapter contract in which capabilities are declared per adapter rather than assumed by the
caller. A `Protocol` describes the surface (load, unload, generate, embed), an immutable descriptor
carries the declared capabilities and the known limitations, and a `require` helper refuses a call
that the adapter never claimed to support. The sample adapter streams and cancels but cannot embed,
and it says so.

What it demonstrates: a missing capability becomes a declared limitation and a loud failure, not a
silently degraded result. In a system that talks to several inference runtimes, that difference is
what keeps a compatibility claim honest.

## memory_fit.py

Calculates whether a model fits in memory the operating system reports at runtime. The budget is
weights from total parameters and effective bits per weight, plus a KV cache from layer count, KV head
count, head dimension and element size, plus scratch space, compared against reported memory after a
system reserve and an inference overhead. The result is a state, not a boolean.

What it demonstrates: the same model on the same machine can be viable at one context length and
impossible at another, and the decision must use reported memory rather than a nominal specification.
The numbers printed are arithmetic, not a benchmark.

## adapter_gate.py

Implements the state machine behind promotion and rollback of a learned adapter. A candidate carries a
quality score and a regression share measured on a frozen evaluation set. Promotion requires a gain
above a margin and no regression beyond tolerance. The active version moves to a previous pointer, so
rollback is a pointer change rather than a restore, and every decision appends to an audit trail.

What it demonstrates: a learning system that cannot be reverted is a learning system that cannot be
trusted. The gate is deliberately boring, because the interesting part is the record it leaves behind.

## What these examples are not

They are illustrations, not the product. They have no persistence, no concurrency, no error taxonomy,
no configuration and no tests. The real implementation of these ideas is future work, and the design
documents in `../docs` describe it without claiming that it exists.
