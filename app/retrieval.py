"""Passo 4 — Pesquisa: encontrar os k chunks mais relevantes para uma pergunta."""

from app.schemas import RetrievedChunk
from app.db import get_connection
from pgvector import Vector


def search(query_embedding: list[float], k: int) -> list[RetrievedChunk]:
    sql = """SELECT d.source, c.chunk_index, c.content, c.embedding <=> %s AS distancia
FROM chunks c
JOIN documents d ON d.id = c.document_id
ORDER BY distancia
LIMIT %s"""
    with get_connection() as conn:
        linhas = conn.execute(sql, (Vector(query_embedding), k)).fetchall()
    resultados = []
    for source, chunk_index, content, distancia in linhas:
        resultados.append(RetrievedChunk(
            document_source=source,
            chunk_index=chunk_index,
            content=content,
            score=1-distancia,          
        ))
    return resultados
    

if __name__ == "__main__":
    from app.embeddings import embed_query

    for r in search(embed_query("O que é o modo de túnel?"), 3):
        print(round(r.score, 3), r.document_source, r.chunk_index)
        print(r.content[:150], "\n")