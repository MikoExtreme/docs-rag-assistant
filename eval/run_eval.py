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

import re
import statistics
import sys
from datetime import datetime
from pathlib import Path
 
from app.config import get_settings
from app.generation import _call_llm, answer_question


FRASE_RECUSA = "Não encontrei esta informação nos documentos."
RESULTS_DIR = Path("eval/results")

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


def _imprimir_resumo(registos: list[dict], versions: list[str]) -> None:
    for versao in versions:
        rs = [r for r in registos if r["versao"] == versao]
        sem = [r for r in rs if not r["answerable"]]
        com = [r for r in rs if r["answerable"]]
        lat = [r["latencia_s"] for r in rs]
        print(f"\n=== {versao} (k={rs[0]['k']}) ===")
        print(f"sem resposta: {sum(r['recusou'] for r in sem)}/{len(sem)} com a frase de recusa")
        print(f"com resposta: {sum(r['recusou'] for r in com)}/{len(com)} recusaram (por engano)")
        print(f"com resposta: {sum(r['tem_citacao'] for r in com)}/{len(com)} com citação [n]")
        print(
            f"tokens médios: {statistics.mean(r['tokens_entrada'] for r in rs):.0f} entrada / "
            f"{statistics.mean(r['tokens_saida'] for r in rs):.0f} saída"
        )
        print(f"latência: média {statistics.mean(lat):.1f} s, mediana {statistics.median(lat):.1f} s")


def compare_prompts(questions_path: str, versions: list[str], k: int | None = None) -> None:
    """Corre as perguntas com cada versão do prompt e guarda os resultados em eval/results/.
 
    Julgamento (ver README):
    - automático: a resposta contém a frase de recusa? tem citações [n]?
      (a frase de recusa só faz sentido na v2: a v1 não a conhece)
    - manual: eu leio as respostas no ficheiro de revisão e marco se estão certas.
    """
    with open(questions_path, encoding="utf-8") as f:
        perguntas = [json.loads(linha) for linha in f]
    if k is None:
        k = get_settings().top_k
 
    # Aquecimento: a 1.ª chamada ao Ollama carrega o modelo e não deve entrar na latência.
    _call_llm("Responde apenas: ok")
 
    registos = []
    for versao in versions:
        for i, q in enumerate(perguntas, start=1):
            resposta = answer_question(q["question"], k=k, prompt_version=versao)
            registos.append({
                "versao": versao,
                "pergunta": q["question"],
                "answerable": q["answerable"],
                "k": k,
                "resposta": resposta.text,
                "recusou": FRASE_RECUSA in resposta.text,
                "tem_citacao": bool(re.search(r"\[\d+\]", resposta.text)),
                "fontes": [f"{c.document_source}#{c.chunk_index}" for c in resposta.sources],
                "tokens_entrada": resposta.input_tokens,
                "tokens_saida": resposta.output_tokens,
                "latencia_s": resposta.latency_seconds,
            })
            print(f"[{versao}] {i}/{len(perguntas)} feita")
 
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
 
    caminho_json = RESULTS_DIR / f"compare_{carimbo}.jsonl"
    with open(caminho_json, "w", encoding="utf-8") as f:
        for r in registos:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
 
    caminho_rev = RESULTS_DIR / f"revisao_{carimbo}.md"
    with open(caminho_rev, "w", encoding="utf-8") as f:
        f.write("# Revisão manual\n\nPreenche 'Correta?' com sim / não / parcial.\n\n")
        for q in perguntas:
            tipo = "com resposta nos documentos" if q["answerable"] else "SEM resposta nos documentos"
            f.write(f"## {q['question']}\n_{tipo}_\n\n")
            if q.get("must_contain"):
                f.write("Deve conter: " + " | ".join(q["must_contain"]) + "\n\n")
            for r in registos:
                if r["pergunta"] == q["question"]:
                    f.write(f"**{r['versao']}** (fontes: {', '.join(r['fontes'])})\n\n")
                    f.write(r["resposta"] + "\n\n")
                    f.write("Correta? \n\n")
 
    _imprimir_resumo(registos, versions)
    print(f"\nResultados: {caminho_json}\nRevisão manual: {caminho_rev}")


if __name__ == "__main__":
    if "compare" in sys.argv[1:]:
        compare_prompts("eval/questions.jsonl", ["v1", "v2"])
    else:
        for k in (1, 3, 5):
            ficheiro, chunk = hit_rate_at_k("eval/questions.jsonl", k)
            maximo = max_hit_rate_at_k("eval/questions.jsonl", k)
            print(f"k={k}: ficheiro {ficheiro:.2f}, chunk {chunk:.2f} (máximo possível {maximo:.2f})")









"""Avaliação do pipeline.
 
Uso (a partir da raiz do repositório):
    python -m eval.run_eval            # hit rate@k da pesquisa (k = 1, 3, 5)
    python -m eval.run_eval compare    # compara os prompts v1 e v2 (precisa do Ollama aberto)
 
Formato de eval/questions.jsonl (uma pergunta por linha):
    {"question": "...", "answerable": true, "expected_sources": ["ficheiro.docx"],
     "must_contain": ["frase que a resposta certa tem de conter"]}
 
Métricas de pesquisa: acerto de ficheiro e acerto de chunk, com o máximo possível.
Comparação de prompts: ver compare_prompts. Os resultados vão para eval/results/.
"""