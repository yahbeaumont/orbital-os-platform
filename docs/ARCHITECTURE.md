# Architecture

The architecture established during the study. Nothing described here is implemented. Proposals
depend on a measurement not yet taken, and unverified items are marked as such.

## 1. Context

ORBITAL OS is a desktop application, not a service and not an operating system. A user installs it on
one machine, and that machine is the whole deployment. Three consequences shape everything else.

The core is a library with a process of its own. The interface is a client of the engine through an
internal contract, and the same engine is reachable as an importable package, a command line tool and
a local HTTP API. An engine born inside the interface process would have to be rewritten whenever the
interface changed.

State is local and canonical. Database, model cache, logs, memory and audit trail live on the user's
disk, so backup is a file copy and deletion is a data model requirement.

Installation is part of the product. A missing runtime, an assisted install, an integrity check and a
fallback to a tested alternative are normal paths, not exceptional error handling.

## 2. Shape

A modular monolith: one installable product, modules separated by package, communicating only through
typed contracts validated at each boundary. No microservices, no distributed queue, no external
service required for the product to function. Six layers and one dependency rule:

```
Interface → Boundary → Orchestration → Cognition → Execution → Foundation
```

A layer may depend on the layers below it and never on those above. Hardware detection, the registry
and the runtime layer do not know that an interface exists, and the API gateway knows only the public
surface of the Intelligence Engine. An import graph test enforces the rule, so an inversion fails the
build instead of surviving a review.

| Layer | Modules |
| --- | --- |
| Interface | Desktop interface |
| Boundary | API Gateway, command line |
| Orchestration | Intelligence Engine, Routing Engine, Agent Runtime |
| Cognition | Memory, Experience, Learning, Evaluation |
| Execution | Hardware Detection, Compatibility Engine, Model Registry, Model Manager, Model Runtime |
| Foundation | Policy Engine, configuration, structured logging, paths, local storage |

## 3. Responsibilities and contracts

| Module | Responsibility |
| --- | --- |
| Hardware Detection | Layered inventory plus a functional test per acceleration API |
| Compatibility Engine | Memory budget and a six-state verdict per model and machine |
| Model Registry | Catalog with provenance, separating discovery, installation and execution |
| Model Manager | Official download, checksum, deduplicated cache, safe removal |
| Model Runtime | Adapter contract over llama.cpp, Ollama, vLLM, Transformers and optional MLX |
| Intelligence Engine | Request interpretation, orchestration, standardized response |
| Routing Engine | Model and runtime choice from intent, cost, budget and history |
| Memory Engine | Four memory types, hybrid retrieval, retention, complete deletion |
| Experience Engine | Selective, consented recording of interactions |
| Learning Engine | Reversible quick layer and gated adapter layer |
| Evaluation Engine | Evaluation sets, paired comparison, regression detection |
| Policy Engine | Default-deny decisions, approvals, append-only audit |
| Agent Runtime | Run, Task, Tool, Approval, Event, Artifact, deterministic scheduler |
| API Gateway | Declared OpenAI-compatible subset, streaming, local authentication |
| Interface | Client of the engine, no canonical state |

Four contracts carry the argument.

The compatibility contract takes a model specification and a hardware report and returns a verdict.
The arithmetic is explicit: resident weights from total parameters and effective bits per weight, KV
cache from batch, context, layer count, KV heads, head dimension and element size, then scratch,
runtime overhead and a system reserve. Layer and head metadata come from the artifact, never from an
illustrative archetype. Six states are mandatory: tested, not validated, compatible with limitations,
incompatible, requires installation, requires additional hardware.

The runtime contract covers discovery, installation, load, configure, generate with streaming and
cancellation, embed, metrics and diagnose. Capabilities are declared per method, and a limitation is
declared rather than simulated. Runtime selection belongs to the routing engine.

The learning contract splits reversible from irreversible work. Quick learning writes only
inspectable artifacts: preferences, context instructions, memories, procedures and routing. Deep
learning produces adapters over a frozen base, in isolation, from a versioned immutable dataset, with
before and after evaluation, a promotion gate, version history and rollback.

The policy contract answers every sensitive question with deny by default, least privilege and
non-amplifying inheritance. Approvals bind payload, resource, tool and validity, and the audit trail
is append-only and revocable.

## 4. One request

A request enters through the interface, the command line or a compatible client. The gateway asks the
policy engine whether the action is permitted and with which scope. The Intelligence Engine resolves
intent, complexity and a context budget. The Memory Engine returns consented context with origin
attached. The Routing Engine selects a model, a runtime and a fallback chain, using the compatibility
verdict and the memory budget as inputs. The adapter loads and configures the artifact and generates
with streaming while reporting metrics. The response leaves with its execution record. The Experience
Engine records the interaction only where consent exists, and learning work is queued outside the
request path.

Installation follows the same pattern: catalog entry, compatibility assessment against the real
artifact, memory budget shown to the user, official download with checksum, registration, a short
functional test, then either the installed state or an installed-with-limitation state with a readable
diagnosis.

## 5. Conceptual data model

A hardware report produces device and capability records. A model record points to artifacts, each
with a format, a quantization and a digest. A validation record joins an artifact, a runtime version,
a backend and a device to an environment description and an outcome. Compatibility verdicts are
derived from validation records and the current hardware report, never stored as a standalone claim.
A conversation produces events; events selected under consent become memory records, and records
referenced by an authorized dataset become dataset entries. A dataset version produces an adapter
version, which points to a base revision, an evaluation run and a promotion decision. Policy
decisions and approvals form an append-only chain referencing the action they authorized.

Every compatibility claim traces to an environment record, and every learned artifact traces to a
dataset, a base revision and a promotion decision.

## 6. Deployment

The engine ships as a Python wheel plus per-platform sidecars. The desktop shell is proposed as Tauri 2
with the engine as a sidecar process, conditional on a prototype measuring memory, installer size,
process behaviour and webview cost on all three operating systems. Packaging starts with PyInstaller
and compares Nuitka. Builds run on native runners per platform, because cross compilation is not
available, and the updater verifies signatures. Continuous integration runs lint, types and tests on
Linux, Windows and macOS, and reports hardware-dependent tests as not executed rather than omitting
them.

## 7. Known limits

Nothing here has been executed. The compatibility formula is fixed but uncalibrated: overhead figures
are a starting reserve until per-backend instrumentation replaces them. The vector index is undecided
and will be chosen by local benchmark, and the desktop shell is a hypothesis. Hardware qualification
requires machines the development environment does not have, so no state can reach "tested" yet.
Vendor-declared performance figures were not reproduced, and the memory capacity of one configuration
could not be confirmed in a primary public source, which is why the engine reads capacity at runtime.
