"""
rag.py — Embedding, vector storage, retrieval, and LLM generation for
the CSULB CS Professor Unofficial Guide.

Milestone 4: embed chunks into ChromaDB, retrieve by cosine similarity.
Milestone 5: generate grounded answers via Groq (Llama 3.3 70B).
"""

import json
import os

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── Chunk loading ────────────────────────────────────────────────────

def load_chunks(path: str = "documents/chunks.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Embedding model ──────────────────────────────────────────────────

def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


# ── Vector store ─────────────────────────────────────────────────────

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "csulb_reviews"


def build_vector_store(chunks: list[dict] | None = None) -> chromadb.Collection:
    """Embed all chunks and upsert into a persistent ChromaDB collection.

    Skips re-embedding when the collection already has the correct count.
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if chunks is None:
        chunks = load_chunks()

    # Skip if already populated with the right number of chunks
    if collection.count() == len(chunks):
        print(f"Collection already has {collection.count()} chunks — skipping embedding.")
        return collection

    print(f"Embedding {len(chunks)} chunks...")
    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    # Batch upsert in groups of 100
    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        end = min(start + batch_size, len(chunks))
        batch_ids = [f"chunk_{i:04d}" for i in range(start, end)]
        batch_embeddings = embeddings[start:end].tolist()
        batch_documents = texts[start:end]
        batch_metadatas = [
            {
                "professor": c["professor"],
                "course": c["course"],
                "source_url": c["source_url"],
                "source_type": c["source_type"],
            }
            for c in chunks[start:end]
        ]
        collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )

    print(f"Upserted {len(chunks)} chunks into ChromaDB.")
    return collection


def get_collection() -> chromadb.Collection:
    """Return the existing ChromaDB collection (no embedding)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(name=COLLECTION_NAME)


# ── Retrieval ────────────────────────────────────────────────────────

def retrieve(query: str, k: int = 8) -> dict:
    """Embed the query, search ChromaDB, return top-k results with distances."""
    model = get_embedding_model()
    query_embedding = model.encode([query])[0].tolist()

    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    return results


# ── Generation ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are the CSULB CS Professor Guide, a helpful assistant that answers \
questions about Computer Science professors and courses at California State \
University, Long Beach.

Rules:
1. Answer ONLY based on the student reviews provided below. Do not use \
outside knowledge about professors or courses.
2. If even ONE review contains a direct answer to the question, use it. \
Only say "I don't have enough information in the reviews to answer that" \
when NONE of the reviews address the question at all.
3. When students disagree in their reviews, present both sides fairly — but \
still provide a clear answer based on what the reviews say.
4. Be concise and direct. Summarize across multiple reviews when possible.
5. Do NOT fabricate source URLs or citations — the system will attach sources \
automatically.\
"""


def _build_user_prompt(query: str, chunks: list[dict]) -> str:
    """Format retrieved chunks as a numbered context block for the LLM."""
    context_lines = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", chunk)
        prof = meta.get("professor", "unknown")
        course = meta.get("course", "unknown")
        text = chunk.get("document", chunk.get("text", ""))
        context_lines.append(f"[{i}] (Professor: {prof}, Course: {course})\n{text}")

    context_block = "\n\n".join(context_lines)
    return f"Student reviews:\n\n{context_block}\n\nQuestion: {query}"


def generate_answer(query: str, chunks: list[dict]) -> str:
    """Call Groq LLM with retrieved context and return the answer text."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    user_prompt = _build_user_prompt(query, chunks)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def ask(query: str, k: int = 8) -> dict:
    """Full RAG pipeline: retrieve → generate → attach deduplicated sources."""
    results = retrieve(query, k=k)

    # Flatten ChromaDB results into a list of chunk dicts
    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    answer = generate_answer(query, chunks)

    # Programmatic source attribution — deduplicated
    seen = set()
    sources = []
    for chunk in chunks:
        meta = chunk["metadata"]
        key = (meta["source_url"], meta["professor"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "url": meta["source_url"],
                "source_type": meta["source_type"],
                "professor": meta["professor"],
            })

    return {"answer": answer, "sources": sources}


# ── CLI test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Building / loading vector store...")
    build_vector_store()

    test_queries = [
        "Are Prof. Neal Terrel's exams multiple-choice or free-response in CECS 323?",
        "Is attendance mandatory for CECS 491B with Professor Frank Murgolo?",
        "How heavy is the workload for Neal Terrel's classes?",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")

        results = retrieve(query, k=5)
        for i in range(len(results["ids"][0])):
            doc = results["documents"][0][i]
            dist = results["distances"][0][i]
            meta = results["metadatas"][0][i]
            preview = doc[:200] + "..." if len(doc) > 200 else doc
            print(f"\n  [{i+1}] distance={dist:.4f} | "
                  f"professor={meta['professor']} | course={meta['course']}")
            print(f"      {preview}")
