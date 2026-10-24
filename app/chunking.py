"""Passo 2 — Chunking: partir um documento em pedaços para indexar.

É aqui que muita da qualidade do RAG se decide. Vale a pena experimentar e
registar no README o que testaste (tamanho, overlap, por parágrafo vs. por caracteres).
"""


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide `text` em chunks de ~`chunk_size` caracteres com `overlap` de sobreposição.

    TODO(Pedro): implementar e decidir o que fazer com cortes a meio de frases.
    """
    raise NotImplementedError
