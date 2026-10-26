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

Requisitos: Python 3.11 ou superior (testado em 3.11 localmente e em 3.12 no CI), Docker.

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


- **Documentos:** 8 documentos `.docx` (resumos próprios de cibersegurança), entre 199 e 2 930 caracteres.
- **Perguntas:** quantas, como foram escritas, e onde estão (`eval/questions.jsonl`) (TODO).
- **Hit rate@k:** valores para k = ... (TODO).
- **Comparação de prompts:** v1 vs v2 e como julguei as respostas (TODO).
- **Custo e latência:** média por pergunta (TODO).


### Tamanho dos chunks

O modelo de embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) lê no máximo 128 tokens,
e o excesso é ignorado. Medi o número de tokens dos chunks do corpus (8 documentos):

| Configuração | Chunks | Máximo de tokens | Chunks acima de 128 |
|---|---|---|---|
| 300 caracteres, overlap 50 | 39 | 126 | 0 |
| 800 caracteres, overlap 100 | 16 | 296 | 12 |

Com 800 caracteres, 12 de 16 chunks excediam o limite e seriam truncados no embedding.
Escolhi 300 com overlap de 50. O máximo de 126 tokens fica no limite, por isso não aumentei
o tamanho. O hit rate@k de cada configuração está na lista acima (por preencher).

Observação: com um único par de frases de teste, a semelhança coseno entre duas frases
sobre o mesmo tema foi 0,38 e entre frases de temas diferentes 0,22. É um exemplo isolado,
não uma medida de qualidade do modelo.


## Onde falhou e porquê

_Por preencher — só depois de analisar as respostas erradas._ Para cada falha:
a pergunta, o que o sistema respondeu, a causa provável (chunking? pesquisa? prompt?)
e o que mudei ou deixei por resolver (TODO).

## Limitações

- O corpus é muito pequeno (8 documentos curtos, 39 chunks com 300/50). Com tão poucos chunks, um k alto devolve uma fração grande do corpus, por isso os valores de hit rate@k só são informativos para k pequeno (1 ou 3).
