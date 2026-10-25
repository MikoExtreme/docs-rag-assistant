"""Explora o chunking nos documentos reais.

Uso (na raiz do repositório):
    python -m scripts.explore_chunking
"""

from pathlib import Path

from app.chunking import chunk_text
from app.ingest import load_documents

TAMANHOS = [(300, 50), (800, 100)]   # pares (chunk_size, overlap) a comparar

docs = load_documents(Path("data/docs"))

for chunk_size, overlap in TAMANHOS:
    print(f"\n=== chunk_size={chunk_size}, overlap={overlap} ===")
    total = 0
    for doc in docs:
        chunks = chunk_text(doc.text, chunk_size, overlap)
        total += len(chunks)
        print(f"{doc.source}: {len(doc.text)} caracteres -> {len(chunks)} chunks")
    print(f"TOTAL: {total} chunks")

# Para veres os chunks de um documento (muda o nome e os valores à vontade):
doc = next(d for d in docs if d.source == "VPN.docx")
for i, c in enumerate(chunk_text(doc.text, 300, 50)):
    print(f"\n--- chunk {i} ({len(c)} caracteres) ---")
    print(c)