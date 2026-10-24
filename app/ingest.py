"""Passo 1 — Ingestão: ler ficheiros, partir em chunks, gerar embeddings, guardar na BD.

Este ficheiro orquestra os outros passos (chunking.py, embeddings.py, db.py).
"""

from pathlib import Path

from app.schemas import Document


def load_documents(docs_dir: Path) -> list[Document]:
    """Lê os ficheiros de `docs_dir` (ex.: .md e .txt) e devolve uma lista de Document.

    TODO(Pedro): decidir que formatos suportas e como extrais o título.
    """
    raise NotImplementedError


def ingest_directory(docs_dir: Path) -> int:
    """Pipeline completo de ingestão. Devolve o número de chunks guardados.

    Sugestão de passos: load_documents -> chunk_text -> embed_texts -> INSERT.
    Pensa em como tornar isto idempotente (correr duas vezes não duplica dados).

    TODO(Pedro): implementar.
    """
    raise NotImplementedError
