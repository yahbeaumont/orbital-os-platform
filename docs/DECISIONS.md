# Decisions

Seven architecture decision records from the study, condensed. Each keeps the shape used in the
private repository: context, decision, alternatives considered, consequences. The dates are the dates
of the original records. None of these decisions has been exercised in running code.

---

## ADR-0001 Modular monolith with explicit contracts

**Status:** accepted. **Date:** 2026-11-21.

**Context.** The product ships to end users on three operating systems and carries fifteen modules
across engine, runtimes, registry, memory, learning, evaluation, policy, agents, API and interface. It
has to install as one thing, be diagnosable from a log, and grow one task at a time without a cloud
dependency.

**Decision.** Build one installable product whose modules are separated by package and communicate
only through typed data contracts validated at each boundary. Hardware, registry and runtime know
nothing about the interface or agents. The API and the interface know only the public surface of the
Intelligence Engine. Any module can be replaced by a competing implementation without touching the
others, provided the contract holds.

**Alternatives considered.** Local microservices were rejected because operating and installing a
service mesh for a single-user desktop application buys latency and partial-failure modes with no
benefit. A single library without internal boundaries develops quickly and then couples everything,
which makes swapping a runtime impossible. A plugin architecture with an empty core was rejected as
excessive flexibility for a product with a known scope.

**Consequences.** Boundaries must be defended in tests, not in review comments: cross-module imports
of internals fail the build. Each task in the plan maps to a package, the product installs as one
unit, and the engine remains usable without the interface. Extraction of a module into its own
process stays possible at the cost of packaging work.

---

## ADR-0002 Universal inference layer with runtime adapters

**Status:** accepted. **Date:** 2026-11-21.

**Context.** The product must run on AMD, NVIDIA, Intel, Apple and plain CPU, on Linux, Windows and
macOS. Each inference runtime is strong on a different combination, and none covers all of them with
the same guarantees. Binding the application to one runtime, or to one vendor, contradicts the reason
the product exists.

**Decision.** Define a runtime contract covering discovery, assisted installation, load, unload,
configuration of context, quantization and sampling, generation with streaming and cancellation,
embedding, status, metrics and diagnosis. Implement one adapter per runtime: llama.cpp as primary,
Ollama, vLLM and Transformers as additional coverage, MLX as an optional adapter on Apple hardware.
Capabilities are declared per method. An adapter that cannot implement a method faithfully declares
the limitation; simulating it is a test failure. Runtime selection belongs to the routing engine,
with the compatibility verdict as input, never to the caller.

**Alternatives considered.** llama.cpp alone covers a great deal but leaves high-throughput serving
on dedicated GPUs and the low-friction path where Ollama is already installed. Ollama alone hides the
memory, context and quantization controls that decide compatibility, and limits hardware to what it
supports. A minimal chat-completions abstraction would discard exactly the controls that make the
difference between a model that runs and one that crashes.

**Consequences.** Every adapter needs its own validation state per operating system, backend and
device, and maintenance cost scales with the number of live adapters. The initial list is therefore
short. An adapter without real test coverage is disabled with a visible compatibility note rather than
kept as nominal support.

---

## ADR-0003 Learning never mutates base weights

**Status:** accepted. **Date:** 2026-11-21.

**Context.** The product promises to improve with use. The direct implementation, training the base
model on the user's activity, is also the most dangerous: catastrophic forgetting, silent degradation,
feedback poisoning, high cost, no rollback, and private data absorbed into weights that can neither be
audited nor deleted. Deleting logs does not delete what the weights retained.

**Decision.** Never modify base weights automatically. Split learning into two layers with different
privileges. Quick learning writes only reversible, human-readable artifacts: preferences, context
instructions, memories, procedures and routing configuration, each with origin, author, version and an
undo path. Deep learning produces adapters over a frozen base, trained in an isolated environment from
a versioned immutable dataset, with paired before and after evaluation, a statistical gate,
controlled promotion, version history and rollback. A single interaction never causes a permanent
change, and automatic promotion is prohibited by default.

**Alternatives considered.** Fine-tuning the base with usage data was rejected for the loss of
rollback, the forgetting risk, the contamination risk and the impossibility of honouring a deletion
request. Prompt and context only was rejected because it discards real per-user specialization, which
is what the gate exists to authorize. Adopting an existing continuous-learning engine as a dependency
was rejected on maturity and unvalidated hardware support; the concepts were reused, the code was not.

**Consequences.** Evaluation and versioning infrastructure is required from early on, so the
Evaluation Engine is not an accessory. The interface must show the active adapter version, its
evaluation and a reversal control. Improvement is bounded by what adapters can deliver. The policy is
guarded by a test, because it becomes irreversible the moment someone trains the base.

---

## ADR-0004 Consent as a precondition for collection, retention and learning

**Status:** accepted. **Date:** 2026-11-21.

**Context.** The memory and experience engines exist to record interactions, and the interface shows
memory and learning metrics. If that becomes automatic capture of everything, the product contradicts
its own privacy claim. The research also found that several ready-made agent memory libraries default
to remote providers, which is unacceptable as silent behaviour in a local-first product.

**Decision.** Five rules. Local by default: no data leaves the host without an explicit, named,
audited action, and a dependency that performs egress by default does not enter without a disabled
flag and a warning. Selective capture: recording requires consent per purpose, meaning memory,
evaluation or training, and consent is revocable with effect on future use and a review of past use.
Configurable retention: expiry per memory type, export in an open format, and deletion that reaches
primary storage, full-text index, vector index, KV cache, pre-processing, write-ahead and shared
memory files, exports and backups. Traceability: every memory and every dataset entry keeps origin,
timestamp and selection rationale, so the system can answer why it knows something. Audit: access to
personal data is logged and the user can inspect, edit and erase.

**Alternatives considered.** Capture everything and filter later was rejected because it contradicts
the promise, widens the exposure surface and makes deletion a matter of luck. Adopting a memory
framework as a central dependency was rejected for its remote defaults, its retention model and its
unenforceable deletion; the taxonomy was borrowed, not the ownership of the data. A single consent
prompt at installation cannot cover distinct purposes or support real revocation.

**Consequences.** Deletion becomes a testable requirement in several places, and the learning dataset
needs immutable versioning. That is more work than storing everything and deciding later. Tightening
is always reversible; loosening is not, so any relaxation requires a new record and a risk review.

---

## ADR-0005 Research and architecture before implementation

**Status:** accepted. **Date:** 2026-11-21.

**Context.** The execution plan states that functionality should not be built before the architecture
is established. Writing runtime, catalog and memory code first would embed vendor decisions in the
core, which is the exact outcome the project exists to avoid.

**Decision.** The first phase was executed as verifiable research: fourteen independent fronts, each
with a report in the private repository, primary open sources rather than search snippets, and a
mandatory verification field per claim, either verified, partially verified or not verified. No
product functionality was implemented before that phase closed. A technical decision that changes a
contract, the stack or a compatibility promise becomes a decision record with evidence, and the
project context document is updated in the same delivery.

**Alternatives considered.** Prototyping immediately with a single runtime was rejected because the
prototype becomes the architecture: vendor choices, data model and API leak into the whole codebase.
Research narrated without artifacts was rejected because it cannot be refuted or reused, and
versioned evidence is what supports both decisions and later review.

**Consequences.** Several corrections arrived before any code existed: one model in the initial
catalog is not locally executable, the NPU is not a general inference route, Vulkan precedes ROCm on
the target AMD platform, and long-context KV footprint rules out configurations that the product
material implied. The cost is calendar time at the start, offset by avoided rework. Research is not
irreversible: new evidence can replace a record, and the replaced record stays marked as such.

---

## ADR-0006 Compatibility declared only with test evidence

**Status:** accepted. **Date:** 2026-11-21.

**Context.** This market mixes marketing claims with engineering claims. Statements such as "runs a
120B model" or "uses the NPU" often fail the arithmetic of memory bandwidth and cache size. The
product runs on hardware the user already owns, so a wrong compatibility claim damages trust in the
product and in the machine.

**Decision.** Compatibility is a verified state, never an inference from a vendor name, a parameter
count or a nominal TOPS figure. Six states are mandatory: tested, not validated, compatible with
limitations, incompatible, requires installation, requires additional hardware. Every state carries
an environment record: operating system and version, kernel and driver, runtime and commit, backend,
device, memory carveout where applicable, artifact hash, quantization, configured context, tested
concurrency, measured metrics and date. Without a record, the highest publishable state is "not
validated". Numbers shown in the interface come from the application's own measurement; a third-party
benchmark may appear as an identified reference, never as a product expectation.

**Alternatives considered.** A hand-maintained static matrix ages at the speed of drivers and hides
the fact that nobody tested it. Running a smoke test and marking the combination compatible ignores
long context, concurrency and stability, and justifies at most "not validated" or "with limitations".
Generic ranges such as "large models" are a polite way of saying nothing while shifting the decision
to the user.

**Consequences.** The product needs instrumentation and a qualification pipeline as permanent work,
and there will be models the application refuses to offer on a given machine. That refusal is correct
behaviour and must appear as such in the interface. Hardening this policy is cheap; loosening it
requires taking information away from the user.

---

## ADR-0007 Engine independent of the interface

**Status:** accepted, with the desktop shell pending a measured prototype. **Date:** 2026-11-21.

**Context.** The engine must remain usable if the interface is replaced by another application or by
a compatible client, and the desktop shell is a cross-platform layer still to be chosen by
measurement. If the engine is born inside the interface process, that replacement costs a rewrite.

**Decision.** Distribute the engine as an importable library and as a local service, with the same
public surface on three paths: a typed internal API, a command line tool and an OpenAI-compatible
gateway. The desktop interface is a client that holds no canonical state and makes no runtime
decision. The initial shell is proposed as Tauri 2 with the Python engine as a sidecar, conditional on
a prototype measuring resident memory, installer size, process behaviour and webview cost on all
three operating systems. The final choice becomes its own record when that prototype exists. The
network surface binds to loopback by default, keeps cross-origin access closed, authenticates even
locally, stores the key as a verifier, and requires an explicit user action with a warning before any
wider reach.

**Alternatives considered.** An engine embedded in the interface process violates the requirement that
the core survive an interface change and couples release cycles. HTTP only, without a library,
removes typing and makes internal testing slow by forcing serialization inside one process. Choosing
Electron without measurement might be right, but it would be a decision made by habit rather than by
data.

**Consequences.** The public contract is versioned, two surfaces must be tested, and the command line
has to stay functional as a diagnostic tool. Swapping the shell affects only the application
directory, which is the point of the decision.
