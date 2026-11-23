# Case study: designing a hardware-agnostic runtime strategy before writing code

## What the work had to produce

ORBITAL OS is a desktop AI platform meant to run on the ORBITAL hardware line and on other vendors'
machines, on three operating systems. Before any of it existed, the project needed a runtime strategy:
which inference engine runs on which machine, how a model is judged to fit in memory, and how the
product keeps learning without becoming unauditable.

The output was documentation: 57 files, roughly 4,000 lines, 14 research reports with primary sources,
7 decision records, 5 diagrams, 5 commits. There is no production code. The value is not the volume: several assumptions died
before they could become architecture.

## The problem, stated concretely

Three questions have to be answered before a single token is generated. What hardware is actually
present? Which runtime can use it? Does this model fit in memory, at this context length, with room
for the operating system?

Each question has a cheap answer that is wrong. Hardware is taken from a specification sheet, but the
sheet describes a product family, not the machine in front of the user. Runtimes are chosen by
reputation, and each has a different story on AMD, NVIDIA, Intel, Apple and plain CPU. Model fit is
estimated from parameter count and a nominal bit width, which ignores the KV cache, the runtime
overhead and the fact that a vendor's "4-bit" file is not four bits per weight.

The failure mode is not a crash on the first request. It is a product that calls a model supported,
downloads tens of gigabytes, answers two questions and dies at token 3,000 when the cache grows. That
is a specification problem, and cheap to prevent on paper.

## Constraints that shaped the design

The product works offline after installation, so the core cannot require a remote service. It must survive the replacement of its interface, so the engine cannot live inside the UI
process. It must be honest about privacy, so memory capture cannot be a default. And it must not depend
on a single vendor, which rules out a build-time runtime choice.

Two constraints were more expensive. Qualification needs hardware the development environment lacks,
so no state can honestly reach "tested". And public performance figures for the platform contradict
each other, turning a benchmarking question into a traceability question.

## The first hard problem: sizing a model against a number nobody agrees on

The product material described two configurations, one with 96 GB of unified memory and one with
192 GB. Public benchmarks for the same processor family were produced on machines with 128 GB. The
vendor's own page, when consulted, listed a lower maximum than the configuration being sold, and the
higher one could not be confirmed in a primary public source.

The tempting response is to pick a number and encode it. The response taken was to remove it from the
software entirely. The compatibility engine computes a budget from memory the operating
system reports at runtime, adds the result of a short functional test per acceleration API, and sizes
the model against that. Resident weights come from total parameters and effective bits per weight, not
active parameters, because sparse activation changes traffic and not residency. The KV cache comes
from the artifact's own layer count, KV head count and head dimension, with the element size made
explicit. Scratch space and runtime overhead are budgeted, and 20 to 25 percent of memory is reserved
for the system and the driver.

This decision has a cost. The software can now be correct on a machine nobody tested, which means it
will sometimes answer "compatible, not validated" on hardware the commercial team considers supported,
and the product cannot answer "does this run on the Ultra?" without that unit on the bench. The
alternative was worse: a constant in the code that is wrong on one of the three configurations.

## The second hard problem: an abstraction written before the implementations

Writing a runtime contract before writing any adapter is a guess about what the runtimes share. The
comparators made that guess visible. One exposes fine control over context, quantization and KV cache
with moderate concurrency. Another hides those controls behind defaults that differ from the first. A
third is built for throughput and does not run natively on one target operating system. A fourth needs
per-architecture code, and a fifth is only meaningful on Apple hardware.

Two properties came out of that comparison. Capabilities are declared per method, so an adapter states
what it can do instead of failing at the call site. And simulation is a defect: an adapter that cannot
stream says so, and the caller sees a declared limitation rather than a plausible-looking response
that is not real. Runtime selection is a routing decision made with the compatibility verdict as
input, never a caller decision, which keeps vendor-specific behaviour out of the product's own
surface.

The trade-off is maintenance. Every adapter carries a validation matrix per operating system, backend
and device, and an untested adapter is worse than no adapter, because it converts an honest refusal
into an incident. The initial list is short, and disabling an adapter is the correct response to
missing coverage.

## The third hard problem: a learning gate with nothing to evaluate yet

"Learns with you" is the feature that most easily destroys credibility, because the obvious
implementation, training the base model on user activity, removes rollback, removal and explanation at
once. The design freezes the base and makes learning produce artifacts: preferences and context
instructions in a reversible layer, versioned adapters in a slower one.

A candidate is compared against the current adapter on a frozen
evaluation set, with paired comparison and a resampling estimate of the difference, plus regression
checks on the capabilities it was not meant to change. Promotion is a recorded decision, and the
previous version stays loadable, so rollback is a pointer change rather than a restore. The design
already shows the cost: the Evaluation Engine has to exist before the Learning Engine is useful, which
reverses the intuitive build order.

## What the research changed

Five conclusions replaced earlier assumptions. A model listed as production-ready is not locally
executable: the official checkpoint has a 552B backbone, roughly 315 GiB of resident weights at the
quantization the plan assumed. Four frontier models have open weights and sit categorically outside
laptop memory, so their place in the catalog is discovery, not execution. The NPU is not a general
inference route for this class of model, because no direct path for the artifact format in use is
documented, so it becomes an optional adapter with an allowlist. On the target AMD platform, Vulkan
precedes ROCm for initial qualification, because the vendor's own documentation limits the ROCm stack
on one operating system. And the memory capacity of the high configuration needs confirmation, with no software impact.

A figure attributed to the hardware, 104 to 128
tokens per second for a model with a 552B backbone and 16B active parameters per token, was never
reproduced and is recorded only as a third-party claim. A bandwidth calculation puts the ideal
decode rate for that active set at roughly 30 tokens per second on the stated memory bandwidth, before
cache, kernels and concurrency. The gap does not prove the claim wrong; it proves the claim has no
recorded conditions. The design response is structural: numbers in the interface come from the
application's own measurement, and a third-party benchmark appears only as an identified reference.

## What I would do differently

The research discipline was worth it, and it ran too long as a single block. A thinner first pass
followed by the smallest slice a user can measure (detect hardware, choose a runtime, load one model,
answer one prompt, expose one endpoint) would have produced the same corrections sooner: half of them
came from arithmetic a running system would have forced anyway.

Second, the compatibility formula should have been executable on day one. It became a small script
that prints weights, cache and budget with the arithmetic visible, and it immediately contradicted two
figures in the product material. A spreadsheet would have hidden the same error.

Third, hardware access should have been a blocking dependency rather than a later logistics item.
Everything here that says "tested" is unattainable, and documentation does not close that
gap.
