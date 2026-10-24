"""Ingere os documentos de data/docs/ na base de dados.

Uso (a partir da raiz do repositório):
    python -m scripts.ingest_docs
"""

from pathlib import Path

from app.ingest import ingest_directory


def main() -> None:
    total = ingest_directory(Path("data/docs"))
    print(f"{total} chunks guardados.")


if __name__ == "__main__":
    main()
