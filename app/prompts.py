"""Passo 5 — Prompts. Guarda cada versão com nome, para as poderes comparar na avaliação."""

from app.schemas import RetrievedChunk

# TODO(Pedro): escrever pelo menos duas versões do prompt (ex.: PROMPT_V1 e PROMPT_V2)
# e medir a diferença com o eval. Pontos a decidir:
#   - como forçar o modelo a responder só com base nos excertos;
#   - o que fazer quando os excertos não chegam para responder;
#   - como pedir citações (formato dos marcadores, ex.: [1], [2]).
PROMPT_V1: str = ""
PROMPT_V2: str = ""


def build_prompt(question: str, chunks: list[RetrievedChunk], version: str = "v1") -> str:
    """Monta o prompt final (pergunta + excertos numerados) para a versão pedida.

    TODO(Pedro): implementar.
    """
    raise NotImplementedError
