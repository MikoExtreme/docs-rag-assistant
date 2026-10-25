"""Passo 3 — Embeddings locais com sentence-transformers.

Requer: pip install -r requirements-ml.txt
Importa o `sentence_transformers` DENTRO das funções (ou com cache), para que o resto
da app e os testes não carreguem o PyTorch sem necessidade.
"""
from functools import lru_cache
from app.config import get_settings

@lru_cache

def _get_model():
    from sentence_transformers import SentenceTransformer   # import aqui dentro de propósito
    return SentenceTransformer(get_settings().embedding_model)                          # o nome do modelo vem de get_settings()

def embed_texts(texts: list[str]) -> list[list[float]]:

    modelo = _get_model()
    vetores = modelo.encode(texts, normalize_embeddings=True)
    return vetores


def embed_query(query: str) -> list[float]:
    pergunta = embed_texts([query])[0]
    return pergunta


if __name__ == "__main__":
    v = embed_query("O que é o modo de túnel?")
    print(len(v))   # deve imprimir 384