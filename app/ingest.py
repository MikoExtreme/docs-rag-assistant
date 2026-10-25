"""Passo 1 — Ingestão: ler ficheiros, partir em chunks, gerar embeddings, guardar na BD.

Este ficheiro orquestra os outros passos (chunking.py, embeddings.py, db.py).
"""

from pathlib import Path
from docx import Document as DocxDocument   

from app.schemas import Document


def _read_docx(caminho: Path) -> str:
    d = DocxDocument(caminho)
    linhas = []
    for p in d.paragraphs:
        linhas.append(p.text)
    for tabela in d.tables:
        for linha in tabela.rows:
            linhas.append(" | ".join(c.text for c in linha.cells))
    return "\n".join(linhas)

def load_documents(docs_dir: Path) -> list[Document]:
    documentos = []
    for caminho in sorted(docs_dir.iterdir()):
        extensao = caminho.suffix.lower()
        if extensao in (".txt", ".md"):
            texto = caminho.read_text(encoding="utf-8")
        elif extensao == ".docx":
            texto = _read_docx(caminho)
        else:
            continue
        documentos.append(Document(source=caminho.name, title=caminho.stem, text=texto))
    return documentos


def ingest_directory(docs_dir: Path) -> int:
    """Pipeline completo de ingestão. Devolve o número de chunks guardados.

    Sugestão de passos: load_documents -> chunk_text -> embed_texts -> INSERT.
    Pensa em como tornar isto idempotente (correr duas vezes não duplica dados).

    TODO(Pedro): implementar.
    """
    raise NotImplementedError


if __name__ == "__main__":
    for doc in load_documents(Path("data/docs")):
        print(doc.source, len(doc.text))