"""Runtime adapter contract with declared capabilities.
Standalone, standard library only. Run: python3 runtime_contract.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Protocol, runtime_checkable


class Capability(str, Enum):
    STREAMING = "streaming"
    CANCELLATION = "cancellation"
    EMBEDDINGS = "embeddings"


class NotDeclared(RuntimeError):
    pass


@dataclass(frozen=True)
class AdapterInfo:
    name: str
    version: str
    capabilities: frozenset[Capability]
    limitations: tuple[str, ...] = ()

    def supports(self, capability: Capability) -> bool:
        return capability in self.capabilities


@runtime_checkable
class RuntimeAdapter(Protocol):
    def info(self) -> AdapterInfo: ...
    def load(self, artifact: str, context_tokens: int) -> None: ...
    def unload(self) -> None: ...
    def generate(self, prompt: str, max_tokens: int) -> Iterator[str]: ...
    def embed(self, text: str) -> list[float]: ...


class SampleGenerator:
    """Adapter that generates but cannot embed."""

    def __init__(self) -> None:
        self._loaded = False

    def info(self) -> AdapterInfo:
        return AdapterInfo(
            name="sample-generator",
            version="0.1",
            capabilities=frozenset({Capability.STREAMING, Capability.CANCELLATION}),
            limitations=("no embedding endpoint", "context fixed at load time"),
        )

    def load(self, artifact: str, context_tokens: int) -> None:
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False
    def generate(self, prompt: str, max_tokens: int) -> Iterator[str]:
        if not self._loaded:
            raise RuntimeError("load() must precede generate()")
        for index in range(min(max_tokens, 3)):
            yield f"<chunk {index}> "

    def embed(self, text: str) -> list[float]:
        raise NotDeclared("sample-generator does not declare embeddings")


def require(adapter: RuntimeAdapter, capability: Capability) -> None:
    if not adapter.info().supports(capability):
        raise NotDeclared(f"{adapter.info().name} does not declare {capability.value}")


def main() -> int:
    adapter: RuntimeAdapter = SampleGenerator()
    print(f"adapter: {adapter.info().name} {adapter.info().version}")
    adapter.load("model.gguf", context_tokens=8192)
    require(adapter, Capability.STREAMING)
    print("output:", "".join(adapter.generate("hello", max_tokens=5)).strip())
    try:
        require(adapter, Capability.EMBEDDINGS)
    except NotDeclared as exc:
        print("refused:", exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
