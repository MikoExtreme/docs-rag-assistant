"""API FastAPI do docs-rag-assistant."""

from fastapi import FastAPI

app = FastAPI(
    title="docs-rag-assistant",
    description="Question-answering assistant over your documents, with cited sources.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Verificação de que a API está de pé (não toca na base de dados nem no modelo)."""
    return {"status": "ok"}


# TODO(Pedro): endpoint POST /ask que recebe {"question": "..."} e devolve a resposta
# com as fontes (usa app.generation.answer_question), e a página HTML simples.
