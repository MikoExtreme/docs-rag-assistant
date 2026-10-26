# docs-rag-assistant

Assistente de perguntas e respostas sobre os teus documentos, com fontes citadas.
RAG com FastAPI, PostgreSQL + pgvector e um modelo local (Ollama, `gemma3:12b`).

> **Estado:** O esqueleto, o CI, a ingestão, a pesquisa e a geração da resposta com citações (prompts e LLM local) estão feitos e avaliados em pequena escala: 20 perguntas, uma corrida por versão de prompt.
> As secções de avaliação abaixo só são preenchidas com números medidos.

## O que é

Projeto de aprendizagem sobre LLMs. Dado um conjunto de documentos, o sistema:

1. parte-os em chunks e gera embeddings localmente (`sentence-transformers`, modelo multilingue);
2. guarda-os no PostgreSQL com pgvector;
3. para cada pergunta, procura os chunks mais relevantes;
4. pede ao `gemma3:12b` (via Ollama, local) uma resposta baseada nesses excertos, **citando as fontes**.

O pipeline não usa LangChain: cada passo é escrito explicitamente, para perceber o que cada um faz.

Usei o Claude (assistente de IA) ao longo de todo o projeto: ajudou-me com a sintaxe e com o código e foi-me explicando cada passo à medida que avançávamos. As perguntas de avaliação e a escolha do tamanho dos chunks são minhas, e fui eu a correr as medições.

**Stack:** Python, FastAPI, PostgreSQL + pgvector (Docker Compose), sentence-transformers,
Ollama (`gemma3:12b`), httpx, pytest, GitHub Actions.

### Estrutura

```
app/        # API e um ficheiro por passo: ingest, chunking, embeddings, retrieval, prompts, generation
data/docs/  # documentos a indexar (só material público/não confidencial)
eval/       # perguntas de avaliação e script de métricas
scripts/    # init.sql (esquema da BD) e scripts de linha de comandos
tests/      # testes (pytest)
```

## Como correr

Requisitos: Python 3.11 ou superior (testado em 3.11 localmente e em 3.12 no CI), Docker,
[Ollama](https://ollama.com).

```bash
# 1. Configuração
cp .env.example .env          # valores por omissão: OLLAMA_HOST=http://localhost:11434, OLLAMA_MODEL=gemma3:12b

# 2. Base de dados (PostgreSQL + pgvector)
docker compose up -d

# 3. Modelo local (o Ollama tem de estar a correr)
ollama pull gemma3:12b

# 4. Ambiente Python
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-ml.txt   # o -ml puxa o PyTorch (grande)

# 5. API
uvicorn app.main:app --reload
curl http://localhost:8000/health
```

Testes:

```bash
pip install -r requirements-dev.txt
pytest
```

Ingestão, geração e avaliação:

```bash
python -m scripts.ingest_docs
python -m app.generation
python -m eval.run_eval
```

Nota: se alterares `scripts/init.sql` (por exemplo a dimensão dos embeddings),
recria a base de dados com `docker compose down -v && docker compose up -d`.

## Como avaliei

- **Documentos:** 8 documentos `.docx` (resumos próprios de cibersegurança), entre 199 e 2 930 caracteres.
- **Perguntas:** 20 perguntas em `eval/questions.jsonl`: 17 com resposta nos documentos e 3 sem resposta (temas vizinhos como o Diffie-Hellman ou o WireGuard, para testar se o assistente inventa; servem na comparação de prompts). Escrevi a maioria usando as palavras dos próprios documentos, o que favorece a pesquisa.
- **Hit rate@k:** ver a secção "Resultados da pesquisa" abaixo.
- **Comparação de prompts:** v1 (instrução simples: "responde com base nos excertos") vs v2 (só excertos; frase fixa "Não encontrei esta informação nos documentos."; citar [1], [2] no fim de cada afirmação; português europeu). A v2 muda várias coisas ao mesmo tempo, por isso uma diferença de resultados não diz qual das alterações a causou. Corri as 20 perguntas com cada versão (k=5, temperatura 0, uma corrida por versão). Julguei de duas formas: automática (a resposta tem a frase de recusa? tem citações `[n]`?) e por leitura das respostas, feita com ajuda de um assistente de IA (Claude), que viu as respostas e a lista de fontes de cada uma, mas não o texto dos excertos: comparou-as com `must_contain` e entre as duas versões. Não verifiquei todas as respostas contra os `.docx`. Resultados abaixo.
- **Custo e latência:** custo em dinheiro = 0 (modelo local). Tokens e latência médios por pergunta na tabela abaixo; a latência é só a da chamada ao modelo (sem embedding nem pesquisa), medida depois de uma chamada de aquecimento.


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


### Resultados da comparação de prompts

Contagens automáticas, nas 20 perguntas (k=5, uma corrida por versão):

| | v1 | v2 |
|---|---|---|
| Sem resposta (3): usou a frase de recusa | 0/3 (não a conhece) | 3/3 |
| Com resposta (17): recusou por engano | 0/17 | 1/17 |
| Com resposta (17): tem citação `[n]` | 11/17 | 16/17 |
| Tokens médios (entrada / saída) | 492 / 99 | 581 / 55 |
| Latência média (mediana) | 4,7 s (4,4 s) | 3,9 s (3,7 s) |

Leitura das 17 respostas com resposta nos documentos:

| | Certa | Parcial | Errada |
|---|---|---|---|
| v1 | 14 | 2 | 1 |
| v2 | 12 | 4 | 1 |

"Parcial" quer dizer que responde a parte do que o documento diz (por exemplo, 2 dos 4 tipos). A "errada" da v2 é a recusa por engano; a da v1 atribui a frase errada (ver "Falhas da geração").

Nas 3 perguntas sem resposta, nenhuma versão inventou uma resposta. A v2 respondeu sempre só com a frase fixa (9 tokens), fácil de detetar automaticamente. A v1 disse por palavras suas que os excertos não tinham a informação; numa delas (Diffie-Hellman) acrescentou que é "um exemplo de técnica de acordo de chaves", o que não vem dos excertos.

Como ler estes números:
- São 17 perguntas com resposta e 3 sem, numa só corrida: 14 contra 12 respostas certas não chega para dizer que uma versão é melhor.
- A v2 cumpre melhor o que pede (frase de recusa, citações, português europeu), mas é mais curta e, nas perguntas de lista, omitiu itens que a v1 trouxe (ver "Falhas da geração"). Gerar menos texto explica parte da menor latência.
- O contador de recusa só faz sentido para a v2. As citações `[n]` medem se existem, não se apontam para o excerto certo (não verifiquei todas), e a diferença é em parte efeito do prompt, porque a v2 as pede explicitamente.
- Português europeu: a v1 usou "senha" numa resposta (em PT-PT, palavra-passe); não encontrei marcas de português do Brasil nas respostas da v2, mas não fiz contagem sistemática.


## Modelo local (Ollama)

Uso o `gemma3:12b` via Ollama, localmente (sem custo por token).

Observações de um teste manual, só com a pergunta e sem excertos nem instruções:

- Responde em português do Brasil ("criptografia", "compartilhada", "você"), não em português
  europeu. A v2 do prompt pede português europeu explicitamente; na comparação de prompts não encontrei marcas de português do Brasil nas respostas da v2 (ver "Resultados da comparação de prompts").
- Sem excertos, responde a partir do que aprendeu no treino. Numa pergunta sobre Diffie-Hellman
  deu uma explicação correta e um exemplo numérico certo, sem ter documento nenhum.
  Isto é o comportamento que o prompt do RAG tem de impedir, sobretudo nas perguntas
  cuja resposta não está nos meus documentos.
- Latência: este teste manual não foi cronometrado; com excertos no prompt, ver "Resultados da comparação de prompts".


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

### Chunks cortados a meio de palavras

O chunking por número fixo de caracteres corta o texto sem respeitar palavras nem frases.
Na pergunta "O que é o modo de túnel?", o excerto que a responde (`VPN.docx`) chega ao
prompt a começar em "acantes passivos conseguem ver quem está a falar", uma palavra cortada.
A pesquisa encontrou o excerto certo (2.º lugar), mas o texto fica mais difícil de ler
e é uma possível fonte de erros na resposta.
Não testei alternativas (por exemplo cortar por parágrafo ou por frase); fica como melhoria.

### Falhas da geração

Observadas na comparação de prompts (respostas lidas com ajuda de um assistente de IA; ver o método acima).

1. **"Onde são usados os pseudorandom numbers?"** — as duas versões atribuem aos números pseudoaleatórios uma frase que, na resposta da v1 à primeira pergunta, descreve a true randomness ("para a geração de keys, mas são demorados e dificultuosos para obter"). Hipótese (não verificada): o início do excerto [1] repete o fim dessa frase por causa do overlap de 50 caracteres, e o modelo não sabe que ela pertence ao parágrafo anterior. A v2 acabou por acrescentar a lista certa (IVs, nonces, salt) a partir de outro excerto; a v1 não.
2. **"Quais são os tipos de autenticação?"** — as duas versões listam só 2 dos 4 tipos (Password-Based e "Based on Biome", palavra cortada no chunk). O "Multifator" parece estar nos mesmos 5 excertos, porque a v1 usou-o noutra pergunta com os mesmos 5 chunks; por isso a omissão é do modelo e não só da pesquisa. Não verifiquei se os "Tokens" estão nesses chunks.
3. **"Que opções de autenticação existem no IPsec…"** — erro de pesquisa: nenhum dos 5 chunks é do `VPN.docx`, onde estão o PSK e o RSA (ponto 3 de "Onde falhou e porquê"). A v2 respondeu "Não encontrei esta informação nos documentos.", o que é falso (a informação existe, só não foi recuperada) e deixou de fora a parte da chave privada, que estava nos excertos. A v1 respondeu só a essa segunda parte e apresentou tipos genéricos de autenticação como se fossem as opções do IPsec, embora tenha começado por dizer que o IPsec não aparece nos excertos.
4. **Listas incompletas na v2:** na pergunta das normas ISO falta a ISO13335, e na dos mecanismos de segurança faltam "Intrusion prevention and detection", "Recovery" e "Ensure secure sharing". A v1 incluiu-as.
5. **Acrescentos que não vêm dos excertos (v1):** na pergunta do transporte e acordo de chaves diz que o transporte envolve "a movimentação física de uma chave", quando o excerto só diz que alguém cria a chave e a transporta para outro; e, na pergunta sobre Diffie-Hellman (sem resposta), a frase já referida.

## Limitações

- O corpus é muito pequeno (8 documentos curtos, 39 chunks com 300/50). Com tão poucos chunks, um k alto devolve uma fração grande do corpus, por isso os valores de hit rate@k só são informativos para k pequeno (1 ou 3).
- Não comparei configurações de chunking pelo hit rate; só medi uma.