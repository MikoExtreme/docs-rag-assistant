from sentence_transformers import SentenceTransformer, util

modelo = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("max_seq_length:", modelo.max_seq_length)

frases = [
    "O modo de túnel esconde o cabeçalho original do pacote.",
    "No IPsec o cabeçalho IP original não é visível para um atacante.",
    "A chave privada é conhecida só pelo seu dono.",
]
v = modelo.encode(frases, normalize_embeddings=True)
print("1 vs 2:", util.cos_sim(v[0], v[1]).item())
print("1 vs 3:", util.cos_sim(v[0], v[2]).item())