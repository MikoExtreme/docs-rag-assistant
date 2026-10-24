"""Passo 3 — Embeddings locais com sentence-transformers.

Requer: pip install -r requirements-ml.txt
Importa o `sentence_transformers` DENTRO das funções (ou com cache), para que o resto
da app e os testes não carreguem o PyTorch sem necessidade.
"""


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Devolve um vetor por texto (dimensão = EMBEDDING_DIM, 384 por defeito).

    TODO(Pedro): carregar o modelo uma só vez (cache) e processar em batches.
    """
    raise NotImplementedError


def embed_query(query: str) -> list[float]:
    """Embedding de uma pergunta. Normalmente igual a embed_texts([query])[0].

    TODO(Pedro): confirma na documentação do modelo se perguntas e documentos
    precisam de tratamento diferente.
    """
    raise NotImplementedError
