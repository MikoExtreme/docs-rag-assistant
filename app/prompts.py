"""Passo 5 — Prompts. Guarda cada versão com nome, para as poderes comparar na avaliação."""

from app.schemas import RetrievedChunk

PROMPT_V1: str = """Responde à pergunta com base nos excertos seguintes.

Excertos:
{contexto}

Pergunta: {pergunta}
"""
PROMPT_V2: str = """Responde à pergunta usando só a informação dos excertos abaixo, sem usar conhecimento próprio.

Regras:
- Cita as fontes com marcadores como [1] e [2], que correspondem aos números dos excertos. Põe o marcador no fim de cada afirmação.
- Se os excertos não chegarem para responder, responde exatamente: "Não encontrei esta informação nos documentos."
- Responde em português europeu (de Portugal), sem brasileirismos.

Excertos:
{contexto}

Pergunta: {pergunta}
"""

PROMPTS = {"v1": PROMPT_V1, "v2": PROMPT_V2}


def build_prompt(question: str, chunks: list[RetrievedChunk], version: str = "v1") -> str:
    partes = []
    for n, c in enumerate(chunks, start=1):          # começa em 1, não em 0
        partes.append(f"[{n}] ({c.document_source})\n{c.content}")
    contexto = "\n\n".join(partes)
    return PROMPTS[version].format(contexto=contexto, pergunta=question)


if __name__ == "__main__":
    from app.embeddings import embed_query
    from app.retrieval import search

    pergunta = "O que é o modo de túnel?"
    chunks = search(embed_query(pergunta), k=3)
    print(build_prompt(pergunta, chunks, version="v2"))