"""Avaliação do pipeline.

Uso (a partir da raiz do repositório):
    python -m eval.run_eval

Formato esperado de eval/questions.jsonl (uma pergunta por linha; vê questions.example.jsonl):
    {"question": "...", "expected_source": "ficheiro.md", "expected_answer": "..."}

Métrica de pesquisa: hit rate@k = fração das perguntas em que o documento esperado
aparece nos k primeiros resultados da pesquisa.
Além disso, regista por pergunta: versão do prompt, tokens, custo estimado e latência.
"""


def hit_rate_at_k(questions_path: str, k: int) -> float:
    """Devolve o hit rate@k sobre o ficheiro de perguntas.

    TODO(Pedro): implementar (usa embed_query + search; não precisa de chamar o Claude).
    """
    raise NotImplementedError


def compare_prompts(questions_path: str, versions: list[str]) -> None:
    """Corre as perguntas com cada versão do prompt e guarda os resultados em eval/results/.

    TODO(Pedro): implementar e decidir como julgas se a resposta está certa
    (à mão, por palavras-chave, ou com um juiz LLM) — e escreve a escolha no README.
    """
    raise NotImplementedError


if __name__ == "__main__":
    raise NotImplementedError("TODO(Pedro): ligar hit_rate_at_k e compare_prompts.")
