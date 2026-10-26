"""Avaliação do pipeline.

Uso (a partir da raiz do repositório):
    python -m eval.run_eval

Formato esperado de eval/questions.jsonl (uma pergunta por linha; vê questions.example.jsonl):
    {"question": "...", "expected_source": "ficheiro.md", "expected_answer": "..."}

Métrica de pesquisa: hit rate@k = fração das perguntas em que o documento esperado
aparece nos k primeiros resultados da pesquisa.
Além disso, regista por pergunta: versão do prompt, tokens, custo estimado e latência.
"""
import json
from app.embeddings import embed_query
from app.retrieval import search
from itertools import combinations
from app.db import get_connection


def hit_rate_at_k(questions_path: str, k: int) -> tuple[float, float]:
    """Devolve (taxa de acerto de ficheiro, taxa de acerto de chunk) para o k dado."""
    with open(questions_path, encoding="utf-8") as f:
        perguntas = [json.loads(linha) for linha in f]
    com_resposta = [q for q in perguntas if q["answerable"]]

    acertos_ficheiro = 0
    acertos_chunk = 0
    for q in com_resposta:
        resultados = search(embed_query(q["question"]), k)

        acerto_ficheiro = any(r.document_source in q["expected_sources"] for r in resultados)
        acerto_chunk = all(
                any(frase in r.content for r in resultados)
                for frase in q["must_contain"]
                )

        if acerto_ficheiro:
            acertos_ficheiro += 1
        if acerto_chunk:                             # o mesmo para o chunk
            acertos_chunk += 1
        if not acerto_chunk:
            print(f"  falhou @k={k}: {q['question']}")            
    return acertos_ficheiro / len(com_resposta), acertos_chunk / len(com_resposta) # o mesmo para o chunk


def min_chunks_needed(frases: list[str], chunks: list[str], max_n: int = 5) -> int | None:
    """Menor número de chunks que, juntos, contêm todas as frases (None se não houver até max_n)."""
    uteis = [c for c in chunks if any(f in c for f in frases)]   # só interessam estes
    for n in range(1, max_n + 1):
        for grupo in combinations(uteis, n):
            if all(any(f in c for c in grupo) for f in frases):
                return n
    return None


def max_hit_rate_at_k(questions_path: str, k: int) -> float:
    """Máximo que o acerto de chunk pode atingir com este k, dado como o corpus foi partido."""
    with open(questions_path, encoding="utf-8") as f:
        perguntas = [json.loads(linha) for linha in f]
    com_resposta = [q for q in perguntas if q["answerable"]]

    with get_connection() as conn:
        chunks = [linha[0] for linha in conn.execute("SELECT content FROM chunks").fetchall()]

    possiveis = 0
    for q in com_resposta:
        n = min_chunks_needed(q["must_contain"], chunks)
        if n is not None and n <= k:
            possiveis += 1
    return possiveis / len(com_resposta)


def compare_prompts(questions_path: str, versions: list[str]) -> None:
    """Corre as perguntas com cada versão do prompt e guarda os resultados em eval/results/.

    TODO(Pedro): implementar e decidir como julgas se a resposta está certa
    (à mão, por palavras-chave, ou com um juiz LLM) — e escreve a escolha no README.
    """
    raise NotImplementedError


if __name__ == "__main__":
    for k in (1, 3, 5):
        ficheiro, chunk = hit_rate_at_k("eval/questions.jsonl", k)
        maximo = max_hit_rate_at_k("eval/questions.jsonl", k)
        print(f"k={k}: ficheiro {ficheiro:.2f}, chunk {chunk:.2f} (máximo possível {maximo:.2f})")