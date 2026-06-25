#!/usr/bin/env python3
"""
Build (or rebuild) the FAISS similarity index from the resume corpus.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --corpus data/full_resumes.csv

This reads a CSV with at least `resume_text` and `Category` columns,
embeds every resume with the configured Sentence-Transformers model,
and writes a FAISS index + metadata sidecar file to disk for the app
to load at startup.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make the project root importable when running this script directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from app.config import get_config  # noqa: E402
from app.services.embedding_service import EmbeddingService  # noqa: E402
from app.services.faiss_index_service import FaissIndexService  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the HireSense AI resume FAISS index.")
    parser.add_argument(
        "--corpus", type=str, default=None,
        help="Path to a CSV with 'resume_text' and 'Category' columns. "
             "Defaults to RESUME_CORPUS_PATH from config.",
    )
    parser.add_argument(
        "--snippet-len", type=int, default=300,
        help="Number of characters of each resume to store as a preview snippet.",
    )
    args = parser.parse_args()

    config = get_config()
    config.ensure_dirs()

    corpus_path = Path(args.corpus) if args.corpus else config.RESUME_CORPUS_PATH
    if not corpus_path.exists():
        print(f"ERROR: corpus file not found at {corpus_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading resume corpus from {corpus_path} ...")
    df = pd.read_csv(corpus_path)
    required_cols = {"resume_text", "Category"}
    if not required_cols.issubset(df.columns):
        print(f"ERROR: corpus must contain columns {required_cols}, found {set(df.columns)}", file=sys.stderr)
        sys.exit(1)

    df = df.dropna(subset=["resume_text"])
    df = df[df["resume_text"].str.strip().str.len() > 50].reset_index(drop=True)
    print(f"Loaded {len(df)} usable resumes across {df['Category'].nunique()} categories.")

    print(f"Loading embedding model '{config.EMBEDDING_MODEL}' ...")
    embedding_service = EmbeddingService(
        model_name=config.EMBEDDING_MODEL, device=config.EMBEDDING_DEVICE, cache=None
    )

    print("Embedding resumes (this may take a minute)...")
    start = time.time()
    texts = df["resume_text"].tolist()
    embeddings = embedding_service.embed_batch(texts)
    elapsed = time.time() - start
    print(f"Embedded {len(texts)} resumes in {elapsed:.1f}s "
          f"({len(texts) / max(elapsed, 1e-6):.1f} resumes/sec).")

    metadata = [
        {
            "id": str(row.get("ID", i)),
            "category": row["Category"],
            "snippet": str(row["resume_text"])[: args.snippet_len].replace("\n", " ").strip(),
        }
        for i, row in df.iterrows()
    ]

    print("Building FAISS index ...")
    index_service = FaissIndexService(
        index_path=config.FAISS_INDEX_PATH, metadata_path=config.FAISS_METADATA_PATH
    )
    index_service.build(embeddings, metadata)
    index_service.save()

    print(f"Done. Index saved to {config.FAISS_INDEX_PATH}")
    print(f"Metadata saved to {config.FAISS_METADATA_PATH}")
    print(f"Index size: {index_service.size} vectors, dimension {index_service.dimension}")


if __name__ == "__main__":
    main()
