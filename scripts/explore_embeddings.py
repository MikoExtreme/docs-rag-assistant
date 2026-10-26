from sentence_transformers import SentenceTransformer, util
from pathlib import Path
from app.chunking import chunk_text
from app.ingest import load_documents

modelo = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("max_seq_length:", modelo.max_seq_length)
docs = load_documents(Path("data/docs"))

for tamanho, overlap in [(300, 50), (800, 100)]:
    chunks = [c for d in docs for c in chunk_text(d.text, tamanho, overlap)]
    tokens = [len(modelo.tokenizer(c)["input_ids"]) for c in chunks]
    acima = sum(1 for t in tokens if t > 128)
    print(f"{tamanho}/{overlap}: {len(chunks)} chunks, máximo {max(tokens)} tokens, {acima} acima de 128")
frases = [
    "O modo de túnel esconde o cabeçalho original do pacote.",
    "No IPsec o cabeçalho IP original não é visível para um atacante.",
    "A chave privada é conhecida só pelo seu dono.",
]
v = modelo.encode(frases, normalize_embeddings=True)
print("1 vs 2:", util.cos_sim(v[0], v[1]).item())
print("1 vs 3:", util.cos_sim(v[0], v[2]).item())