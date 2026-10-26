"""Passo 6 — Geração: pergunta -> pesquisa -> prompt -> Ollama -> resposta com fontes."""

import time

import httpx

from app.config import get_settings
from app.embeddings import embed_query
from app.prompts import build_prompt
from app.retrieval import search
from app.schemas import Answer


def _call_llm(prompt: str) -> tuple[str, int, int]:
    """Chama o Ollama. Devolve (texto, tokens de entrada, tokens de saída)."""
    settings = get_settings()
    try:
        response = httpx.post(
            f"{settings.ollama_host}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=300,
        )
        response.raise_for_status()
    except httpx.ConnectError as e:
        raise RuntimeError(
            f"Não consegui ligar ao Ollama em {settings.ollama_host}. "
            "Está aberto? (ollama serve)"
        ) from e

    data = response.json()
    text = data["message"]["content"]
    input_tokens = data.get("prompt_eval_count", 0)
    output_tokens = data.get("eval_count", 0)
    return text, input_tokens, output_tokens


def answer_question(question: str, k: int | None = None, prompt_version: str = "v1") -> Answer:
    """Pipeline completo: embed_query -> search -> build_prompt -> Ollama.

    A latência medida é só a da chamada ao modelo (não inclui o embedding nem a pesquisa).
    """
    if k is None:
        k = get_settings().top_k

    query_embedding = embed_query(question)
    chunks = search(query_embedding, k)
    prompt = build_prompt(question, chunks, prompt_version)

    start = time.perf_counter()
    text, input_tokens, output_tokens = _call_llm(prompt)
    latency_seconds = time.perf_counter() - start

    return Answer(
        text=text,
        sources=chunks,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_seconds=latency_seconds,
    )


if __name__ == "__main__":
    question = "O que é o modo de túnel?"
    for version in ("v1", "v2"):
        answer = answer_question(question, k=3, prompt_version=version)
        print(f"=== {version} ===")
        print(answer.text)
        print(
            f"[tokens: {answer.input_tokens} entrada / {answer.output_tokens} saída; "
            f"latência: {answer.latency_seconds:.1f} s]\n"
        )