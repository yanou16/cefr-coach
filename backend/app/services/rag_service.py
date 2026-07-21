"""
RAG Service — pedagogical corpus retrieval.

Pipeline:
  YAML corpus → embed (ChromaDB default / OpenAI) → ChromaDB collection
  → metadata pre-filter (cefr_level IN {L, L+1}) → vector top-k → results

Key design: metadata pre-filter happens BEFORE vector similarity.
This guarantees a B1 learner never receives C1 content, regardless of
how semantically similar it is. Pure vector similarity cannot enforce this.

Corpus format (YAML):
  chunks:
    - id: b1_001
      cefr_level: B1
      skill: grammar          # grammar | vocabulary | reading | listening | writing
      topic: present_perfect_vs_past_simple
      content: |
        ...pedagogical explanation...
      common_errors:
        - "..."
"""

import os
import yaml
import pathlib
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

CORPUS_DIR   = pathlib.Path(__file__).parent.parent.parent / "corpus"
DB_DIR       = pathlib.Path(os.environ.get("CHROMA_DIR", str(pathlib.Path(__file__).parent.parent.parent / "chroma_db")))
COLLECTION   = "cefr_corpus"
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")

LEVEL_ORDER  = ["A1", "A2", "B1", "B2", "C1", "C2"]


# ── Embedding function ─────────────────────────────────────────────────────────

def _embedding_function():
    """
    Uses OpenAI text-embedding-3-small via API — no local model, no RAM overhead.
    Falls back to the local ONNX default when OPENAI_API_KEY / LLM_API_KEY is absent.
    """
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        return OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return DefaultEmbeddingFunction()


# ── Corpus loader ──────────────────────────────────────────────────────────────

def _load_corpus() -> list[dict]:
    """Load all chunks from YAML files in corpus/."""
    chunks = []
    for f in sorted(CORPUS_DIR.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        for chunk in data.get("chunks", []):
            chunks.append(chunk)
    print(f"[rag] Loaded {len(chunks)} chunks from {CORPUS_DIR}")
    return chunks


# ── ChromaDB client (lazy singleton) ──────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_collection():
    import chromadb

    DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_DIR))
    ef     = _embedding_function()

    # Get or create collection
    collection = client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ── Indexing ───────────────────────────────────────────────────────────────────

def build_index(force: bool = False) -> int:
    """
    Embed and index all corpus chunks into ChromaDB.
    Skips chunks already in the collection unless force=True.
    Returns number of chunks indexed.
    """
    collection = _get_collection()
    chunks     = _load_corpus()

    if force:
        # Wipe and rebuild
        import chromadb
        DB_DIR_str = str(DB_DIR)
        client = chromadb.PersistentClient(path=DB_DIR_str)
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        # Re-get (creates fresh)
        _get_collection.cache_clear()
        collection = _get_collection()

    existing_ids = set(collection.get()["ids"])
    new_chunks   = [c for c in chunks if c["id"] not in existing_ids]

    if not new_chunks:
        print(f"[rag] All {len(chunks)} chunks already indexed. Use force=True to rebuild.")
        return 0

    documents = []
    metadatas = []
    ids       = []

    for chunk in new_chunks:
        # Text to embed = topic + content (gives semantic richness)
        doc = f"{chunk['topic'].replace('_', ' ')}\n\n{chunk['content'].strip()}"
        documents.append(doc)
        metadatas.append({
            "cefr_level": chunk["cefr_level"],
            "skill":       chunk["skill"],
            "topic":       chunk["topic"],
            "chunk_id":    chunk["id"],
            # Store errors as pipe-separated string (ChromaDB metadata must be scalar)
            "common_errors": " | ".join(chunk.get("common_errors", [])),
        })
        ids.append(chunk["id"])

    # ChromaDB handles batching internally
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[rag] Indexed {len(new_chunks)} new chunks (total: {len(chunks)})")
    return len(new_chunks)


# ── Level adjacency helper ─────────────────────────────────────────────────────

def _adjacent_levels(level: str) -> list[str]:
    """
    Returns the learner's level + one level up.
    A B1 learner retrieves B1 + B2 content (Krashen's i+1).
    An Advanced+ learner (C1/C2) retrieves C1 + C2.
    """
    if level not in LEVEL_ORDER:
        return [level]
    idx = LEVEL_ORDER.index(level)
    next_idx = min(idx + 1, len(LEVEL_ORDER) - 1)
    return list({LEVEL_ORDER[idx], LEVEL_ORDER[next_idx]})


# ── Retrieval ──────────────────────────────────────────────────────────────────

def retrieve(
    level: str,
    query: str,
    skill: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve pedagogical chunks for a learner.

    Args:
        level:  Learner's current CEFR level (e.g. "B1")
        query:  What the tutor is looking for (e.g. "present perfect vs past simple")
        skill:  Optional filter: "grammar" | "vocabulary" | "reading" | "listening" | "writing"
        top_k:  Maximum chunks to return

    Returns:
        List of chunk dicts with keys: id, cefr_level, skill, topic, content, distance
    """
    collection = _get_collection()

    # Step 1: metadata pre-filter — NEVER return content above the learner's reach
    levels = _adjacent_levels(level)
    where: dict = {"cefr_level": {"$in": levels}}
    if skill:
        where = {"$and": [{"cefr_level": {"$in": levels}}, {"skill": {"$eq": skill}}]}

    # Step 2: vector similarity search within filtered set
    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        print(f"[rag] Query error: {e}")
        return []

    # Step 3: format results
    chunks = []
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        chunks.append({
            "id":          meta["chunk_id"],
            "cefr_level":  meta["cefr_level"],
            "skill":       meta["skill"],
            "topic":       meta["topic"],
            "content":     doc,
            "distance":    round(dist, 4),
            "rank":        i + 1,
        })

    return chunks


def retrieve_for_gap(level: str, skill_gap: str) -> list[dict]:
    """
    Convenience wrapper: retrieve chunks targeting a specific skill gap.
    Used by the tutor service when generating exercises.
    """
    return retrieve(
        level=level,
        query=skill_gap,
        top_k=5,
    )


# ── CLI: build index ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Build the RAG corpus index")
    p.add_argument("--force", action="store_true", help="Wipe and rebuild the index")
    args = p.parse_args()
    n = build_index(force=args.force)
    print(f"Done. {n} chunks indexed.")
