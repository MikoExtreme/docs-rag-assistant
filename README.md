# docs-rag-assistant

Assistente de perguntas e respostas sobre os teus documentos, com fontes citadas.
RAG com FastAPI, PostgreSQL + pgvector e a Claude API.

> **Estado:** O esqueleto, o CI, a ingestão e a pesquisa estão feitos e avaliados; a geração da resposta com citações (prompts e LLM) ainda não.
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

Ingestão e avaliação:

```bash
python -m scripts.ingest_docs
python -m eval.run_eval
```

Nota: se alterares `scripts/init.sql` (por exemplo a dimensão dos embeddings),
recria a base de dados com `docker compose down -v && docker compose up -d`.

## Como avaliei

Ainda por preencher: a comparação de prompts e o custo/latência.


- **Documentos:** 8 documentos `.docx` (resumos próprios de cibersegurança), entre 199 e 2 930 caracteres.
- **Perguntas:** 20 perguntas em `eval/questions.jsonl`: 17 com resposta nos documentos e 3 sem resposta (temas vizinhos como o Diffie-Hellman ou o WireGuard, para testar se o assistente inventa; servem na comparação de prompts, ainda por fazer). Escrevi a maioria usando as palavras dos próprios documentos, o que favorece a pesquisa.
- **Hit rate@k:** ver a secção "Resultados da pesquisa" abaixo.
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
o tamanho. O hit rate@k só foi medido com 300/50; não o comparei com 800/100, por isso a escolha assenta na contagem de tokens e não numa comparação de resultados.

Observação: com um único par de frases de teste, a semelhança coseno entre duas frases
sobre o mesmo tema foi 0,38 e entre frases de temas diferentes 0,22. É um exemplo isolado,
não uma medida de qualidade do modelo.


### Resultados da pesquisa

Para cada uma das 17 perguntas com resposta, a pergunta é transformada num vetor e comparam-se
os k chunks mais próximos. Medi dois tipos de acerto:

- **Acerto de ficheiro:** algum dos k chunks vem de um ficheiro esperado.
- **Acerto de chunk:** cada frase de `must_contain` (um trecho que a resposta certa tem de conter)
  aparece em pelo menos um dos k chunks.

Com chunks de 300 caracteres e overlap de 50 (39 chunks):

| k | Acerto de ficheiro | Acerto de chunk | Máximo possível (chunk) |
|---|---|---|---|
| 1 | 1,00 | 0,41 (7/17) | 0,47 (8/17) |
| 3 | 1,00 | 0,71 (12/17) | 1,00 (17/17) |
| 5 | 1,00 | 0,88 (15/17) | 1,00 (17/17) |

O "máximo possível" é o que a métrica permite: calculei, para cada pergunta, o mínimo de chunks
necessários para cobrir todas as suas frases (8 perguntas precisam de 1 chunk, 8 de 2 e 1 de 3).
Com k=1 só 8 das 17 perguntas podem passar, e passaram 7.

Como ler estes números:
- O acerto de ficheiro é quase trivial: com 8 documentos e perguntas que repetem as palavras
  dos documentos, encontrar o ficheiro certo é fácil. A métrica informativa é a de chunk.
- Com k=5 a pesquisa devolve 5 dos 39 chunks (13% do corpus), por isso 0,88 está
  inflacionado pelo tamanho pequeno do corpus.
- Com 17 perguntas, cada uma vale cerca de 6 pontos percentuais; diferenças pequenas
  entre configurações não são significativas.



## Onde falhou e porquê

Pergunta a pergunta, com k=5 só duas falham; com k menor falham mais, quase sempre
porque a resposta está espalhada por vários chunks.

1. **"Onde são usados os pseudorandom numbers?"** — falha com k=1 e k=3 e passa com k=5.
   As duas frases esperadas estão no mesmo chunk, por isso é um erro de ranking: esse chunk
   não ficou entre os 3 primeiros. Hipótese (não verificada): o documento lista onde se usa a
   aleatoriedade em geral (chaves, IVs, nonces, salt), mas a pergunta fala de
   "pseudorandom numbers", o que a aproxima do chunk que define pseudoaleatoriedade.
   A pergunta ficou mal ajustada ao documento.
2. **"Quais são os tipos de autenticação?"** — falha mesmo com k=5. A resposta está em 3 chunks
   diferentes do mesmo documento e os três têm de estar entre os 5 primeiros. É um limite das
   perguntas de lista com chunks de 300 caracteres.
3. **"Que opções de autenticação existem no IPsec e, para a que usa chaves assimétricas,
   que chave usa quem prova a sua identidade?"** — falha mesmo com k=5. Precisa de um chunk
   do documento de VPN (PSK e RSA) e de outro do documento de autenticação (chave privada).
   Uma só pesquisa pela pergunta dificilmente traz chunks de dois documentos diferentes.

As restantes falhas com k pequeno (normas ISO, tipos de avaliação de risco, mecanismos de
segurança, entre outras) precisam de 2 chunks e passam com k=3 ou k=5: são consequência de
a resposta estar partida em vários chunks, e não de erros de pesquisa.

Ficou por resolver: testar chunks maiores (não fiz) nos documentos de lista, subir o k, ou reescrever
as perguntas de um só tema para não dependerem de vários chunks.

## Limitações

- O corpus é muito pequeno (8 documentos curtos, 39 chunks com 300/50). Com tão poucos chunks, um k alto devolve uma fração grande do corpus, por isso os valores de hit rate@k só são informativos para k pequeno (1 ou 3).
- Não comparei configurações de chunking pelo hit rate; só medi uma.
