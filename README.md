# docs-rag-assistant

Assistente de perguntas e respostas sobre os teus documentos, com fontes citadas.
RAG com FastAPI, PostgreSQL + pgvector e a Claude API.

> **Estado:** em desenvolvimento. O esqueleto, o `/health`, o teste e o CI estão feitos;
> o pipeline (chunking, embeddings, pesquisa, prompts) está a ser implementado.
> As secções de avaliação abaixo só são preenchidas com números medidos.

## O que é

Projeto de aprendizagem sobre LLMs. Dado um conjunto de documentos, o sistema:

1. parte-os em chunks e gera embeddings localmente (`sentence-transformers`, modelo multilingue);
2. guarda-os no PostgreSQL com pgvector;
3. para cada pergunta, procura os chunks mais relevantes;
4. pede ao Claude uma resposta baseada nesses excertos, **citando as fontes**.

O pipeline é escrito à mão, sem LangChain, para perceber cada passo.

**Stack:** Python, FastAPI, PostgreSQL + pgvector (Docker Compose), sentence-transformers,
Claude API, pytest, GitHub Actions.

### Estrutura

```
app/        # API e um ficheiro por passo: ingest, chunking, embeddings, retrieval, prompts, generation
data/docs/  # documentos a indexar (só material público/não confidencial)
eval/       # perguntas de avaliação e script de métricas
scripts/    # init.sql (esquema da BD) e scripts de linha de comandos
tests/      # testes (pytest)
```

## Como correr

Requisitos: Python 3.12+, Docker.

```bash
# 1. Configuração
cp .env.example .env          # preenche ANTHROPIC_API_KEY

# 2. Base de dados (PostgreSQL + pgvector)
docker compose up -d

# 3. Ambiente Python
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-ml.txt   # o -ml puxa o PyTorch (grande)

# 4. API
uvicorn app.main:app --reload
curl http://localhost:8000/health
```

Testes:

```bash
pip install -r requirements-dev.txt
pytest
```

Ingestão e avaliação (quando o pipeline estiver implementado):

```bash
python -m scripts.ingest_docs
python -m eval.run_eval
```

Nota: se alterares `scripts/init.sql` (por exemplo a dimensão dos embeddings),
recria a base de dados com `docker compose down -v && docker compose up -d`.

## Como avaliei

_Por preencher — só depois de medir._ Deve incluir:

- **Documentos:** quantos e de que tipo (TODO).
- **Perguntas:** quantas, como foram escritas, e onde estão (`eval/questions.jsonl`) (TODO).
- **Hit rate@k:** valores para k = ... (TODO).
- **Comparação de prompts:** v1 vs v2 e como julguei as respostas (TODO).
- **Custo e latência:** média por pergunta (TODO).

## Onde falhou e porquê

_Por preencher — só depois de analisar as respostas erradas._ Para cada falha:
a pergunta, o que o sistema respondeu, a causa provável (chunking? pesquisa? prompt?)
e o que mudei ou deixei por resolver (TODO).

## Limitações

- Avaliação feita sobre um conjunto pequeno de documentos e perguntas; os números
  indicam tendências, não garantias.
