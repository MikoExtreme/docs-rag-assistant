"""Tipos partilhados entre os passos do pipeline."""

from dataclasses import dataclass, field


@dataclass
class Document:
    source: str  # nome/caminho do ficheiro, usado nas citações
    title: str
    text: str


@dataclass
class RetrievedChunk:
    document_source: str
    chunk_index: int
    content: str
    score: float  # similaridade (maior = mais parecido); define tu a convenção


@dataclass
class Answer:
    text: str
    sources: list[RetrievedChunk] = field(default_factory=list)
    # Para o registo de custo/latência (parte da avaliação):
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_seconds: float | None = None
