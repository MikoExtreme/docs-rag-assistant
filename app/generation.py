"""Passo 6 — Geração: pergunta -> pesquisa -> prompt -> Claude API -> resposta com fontes."""

from app.schemas import Answer


def answer_question(question: str, k: int | None = None, prompt_version: str = "v1") -> Answer:
    """Pipeline completo de resposta.

    Sugestão: embed_query -> search -> build_prompt -> chamada à API (anthropic.Anthropic().messages.create).
    Mede aqui o tempo e lê os tokens de entrada/saída da resposta da API
    para preencheres `latency_seconds`, `input_tokens` e `output_tokens`.

    TODO(Pedro): implementar.
    """
    raise NotImplementedError
