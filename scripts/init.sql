-- Inicialização da base de dados. Corre automaticamente na primeira criação do volume.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    source      TEXT NOT NULL UNIQUE,   -- caminho/nome do ficheiro, usado nas citações
    title       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id           SERIAL PRIMARY KEY,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  INTEGER NOT NULL,      -- posição do chunk dentro do documento
    content      TEXT NOT NULL,
    -- !!! A dimensão TEM de ser igual à do modelo de embeddings (EMBEDDING_DIM no .env).
    -- paraphrase-multilingual-MiniLM-L12-v2 -> 384.
    -- Se mudares de modelo, altera aqui e recria o volume (docker compose down -v).
    embedding    vector(384) NOT NULL,
    UNIQUE (document_id, chunk_index)
);

-- Com 10-30 documentos, a pesquisa exata (sem índice) é rápida e dá resultados
-- mais fiáveis para a avaliação. Só vale a pena um índice com muitos chunks.
-- Se um dia precisares:
-- CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
--     ON chunks USING hnsw (embedding vector_cosine_ops);
