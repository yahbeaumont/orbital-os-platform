# Security and privacy

This document describes the security model established during the architecture phase. It is a design
document. No control described here is implemented, and none of it should be read as a claim about
running software. The section on guarantees states that plainly.

## Assets to protect

Conversations, memories and any personal data the user chooses to record. Model artifacts and the
disk space they consume. The local API key and any credential a tool or an agent is granted. The audit
trail, which has to stay trustworthy even when the user is the attacker. The integrity of the model
base and of the adapters derived from user data. The user's machine, meaning its files, its network
position and its other processes.

## Trust boundaries

Four boundaries matter.

The host boundary. Everything inside the machine is treated as the user's data, and nothing crosses
outward without an explicit, named, audited action. There is no default telemetry, no default remote
provider and no silent update channel.

The process boundary. The engine, the runtime adapters and any tool execution are separate concerns.
The interface is a client and holds no canonical state, so a compromised or replaced interface cannot
become the source of truth.

The model boundary. A model artifact is untrusted input. A downloaded file is verified by checksum
against an official source before it is used, and a model's template, tool parser and metadata are
treated as data to validate, not as instructions to follow.

The tool boundary. An MCP server, a shell command, a file path or a network call reaches outside the
engine's own state. Each is a privileged operation, and the policy engine sits between the request and
the effect.

## Threats considered

Prompt injection through retrieved content, documents or tool output, leading an agent to act beyond
its mandate. Over-broad tool permissions granted once and inherited upward. A local endpoint exposed
to the network by a default binding, and a key that protects some endpoints but not all. Data
exfiltration through a dependency whose default behaviour is a remote service. Silent capture of
conversations that the user believed were private, and deletion that leaves copies in a full-text
index, a vector index, a cache or a backup. Training data poisoning through user feedback or
retrieved text, and a degraded adapter promoted without notice. Model artefacts that execute
unexpected behaviour through their template or their format. Credentials appearing in logs or in
memory records.

Two threats are specific to this product. The first is a compatibility claim that misleads the user
into loading something the machine cannot sustain, which is a reliability problem with a security
consequence when the failure mode is memory exhaustion under load. The second is an isolation claim
that the operating system cannot honour, where the interface says "sandboxed" while the process is
merely restricted.

## Controls designed

**Policy engine, default deny.** Every sensitive action asks for permission and receives a scope or a
refusal. Privilege is minimal, and inheritance never amplifies: a child context cannot hold a
capability its parent did not have. Approvals bind the payload, the resource, the tool and a validity
window, so an approval cannot be replayed against a different request. Decisions and approvals are
appended to an audit trail that supports revocation and is never rewritten in place.

**Capability isolation.** Execution of untrusted work uses what the platform actually provides:
seccomp with Landlock on Linux, AppContainer with job objects on Windows, App Sandbox on macOS. Each
backend declares the capabilities it can enforce. When the platform cannot provide the protection
requested, the operation fails closed with a visible message. The interface must report the protection
actually applied, not the one intended.

**Consent and audit.** Capture of memory, use of data for evaluation and use of data for training are
separate purposes with separate consent, and consent is revocable with effect on future use. Every
memory record and every dataset entry keeps origin, timestamp and selection rationale, so the system
can answer why it knows something and why a given example was used. Access to personal data is logged.

**Local-first data boundary.** The canonical store is a local database in write-ahead mode, with a
full-text index and an interchangeable vector index. Deletion is designed to reach the primary record,
the full-text index, the vector index, KV caches, pre-processing artefacts, write-ahead and shared
memory files, exports and backups. A dependency that performs network egress by default does not enter
the product without a disabled flag and a warning. The local API binds to loopback, keeps cross-origin
access closed, authenticates even on the same machine, stores its key as a verifier rather than as
plaintext, and requires an explicit user action before any wider network reach. Network discovery
announces the service, never a secret.

**Artifact and licence gates.** Downloads come from official sources with checksum verification
before the artifact is marked installed. Model licences are a catalog field, and a model whose licence
requires acceptance is not offered for download before the user accepts it, with the acceptance
recorded.

## What is not guaranteed

Nothing is implemented, so nothing is guaranteed. There is no running service, no binary, no key and
no data store to test, and this repository should not be read as evidence that any of the above works.

Even once implemented, the design cannot promise that isolation equals the platform's best available
protection on every version, because the primitives differ by kernel and by operating system release
and some configurations will degrade. It cannot promise that deleting text removes everything a
derived adapter learned, which is why deletion has to reach adapters and why memorization testing is a
requirement rather than a nicety. It cannot promise that an automatic judge detects every quality
regression. And it cannot promise that a third-party runtime, driver or model behaves as documented.

## Reporting a problem

There is no running product and no security response process attached to this repository. If you find
an error in these documents, an inconsistency between a claim and its stated source, or a design
weakness in the model described above, open an issue on the repository with the section and the
reasoning. Do not include credentials, personal data or details of a third-party system in a public
issue.
