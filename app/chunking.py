"""Passo 2 — Chunking: partir um documento em pedaços para indexar.

É aqui que muita da qualidade do RAG se decide. Vale a pena experimentar e
registar no README o que testaste (tamanho, overlap, por parágrafo vs. por caracteres).
"""


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:

    if overlap >= chunk_size:
        raise ValueError("overlap tem de ser menor que chunk_size")

    passo = chunk_size - overlap
    chunks = []
    for inicio in range(0, len(text), passo):
        pedaco = text[inicio : inicio + chunk_size]
        pedaco = pedaco.strip()
        if not pedaco:
            continue
        chunks.append(pedaco)
    return chunks


if __name__ == "__main__":
    for c in chunk_text("0123456789" * 5, chunk_size=20, overlap=5):
        print(repr(c))