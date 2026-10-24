"""Passo 4 — Pesquisa: encontrar os k chunks mais relevantes para uma pergunta."""

from app.schemas import RetrievedChunk


def search(query_embedding: list[float], k: int) -> list[RetrievedChunk]:
    """Devolve os `k` chunks mais próximos do embedding da pergunta.

    TODO(Pedro): query SQL com pgvector (operador de distância à tua escolha;
    a distância coseno é o habitual com estes modelos) e ligação via app.db.
    """
    raise NotImplementedError
