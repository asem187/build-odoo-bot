"""Ingest Odoo documentation into a local FAISS index.

This script clones the official Odoo repository (or updates it if already
present) and indexes documentation files. It now processes ``.txt``, ``.md``
and ``.rst`` sources to cover a wider range of formats.
"""
import os
from pathlib import Path
import subprocess
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from dotenv import load_dotenv

load_dotenv()

SOURCE_DIR = os.getenv("DOCS_PATH", "data/docs")
INDEX_DIR = os.getenv("INDEX_PATH", "data/index")
REPO_URL = os.getenv("ODOO_DOCS_REPO", "https://github.com/odoo/odoo.git")
REPO_BRANCH = os.getenv("ODOO_DOCS_BRANCH", "master")


def fetch_docs(dest: Path) -> Path:
    """Clone or update the Odoo docs repository."""
    if dest.exists():
        subprocess.run(["git", "-C", str(dest), "pull", "origin", REPO_BRANCH], check=False)
    else:
        subprocess.run(["git", "clone", "--depth", "1", "--branch", REPO_BRANCH, REPO_URL, str(dest)], check=False)
    return dest


def main():
    docs_path = Path(SOURCE_DIR)
    repo_dir = fetch_docs(docs_path)
    docs = []
    for pattern in ("**/*.txt", "**/*.md", "**/*.rst"):
        loader = DirectoryLoader(
            str(repo_dir),
            glob=pattern,
            recursive=True,
            loader_cls=TextLoader,
        )
        docs.extend(loader.load())
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)
    os.makedirs(INDEX_DIR, exist_ok=True)
    vectorstore.save_local(INDEX_DIR)
    print(f"Saved index to {INDEX_DIR}")


if __name__ == "__main__":
    main()
