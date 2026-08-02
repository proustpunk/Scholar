import os
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from groq import Groq

# ---- Models loaded once at import time, not per-call ----

# Single embedding model used consistently for both storing and querying
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Cross-encoder for reranking: scores (question, chunk) pairs jointly
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Persistent Chroma client
chroma_client = chromadb.PersistentClient(path="./chromadb")


def _collection_name(book_id: int, chapter_name: str) -> str:
    return f"book_{book_id}_{chapter_name.replace(' ', '_').lower()}"


def get_or_create_collection(book_id: int, chapter_name: str):
    return chroma_client.get_or_create_collection(name=_collection_name(book_id, chapter_name))


def store_chunks(book_id: int, chapter_name: str, chunks: list):
    """Embed and store chunks in ChromaDB, with metadata for later citation."""
    collection = get_or_create_collection(book_id, chapter_name)

    embeddings = embedding_model.encode(chunks).tolist()

    # stable ids so re-running store_chunks for the same book/chapter
    # doesn't silently collide with a fresh 0..N index each time
    ids = [f"{book_id}_{chapter_name}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"book_id": book_id, "chapter": chapter_name, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )


def retrieve_candidates(book_id: int, chapter_name: str, question: str, k: int = 10):
    """
    Stage 1 — cheap, approximate retrieval.
    Embeds the question, compares against all stored chunk vectors via
    cosine/L2 distance (Chroma's default), returns the k closest chunks.
    Returns list of dicts: {"text": ..., "metadata": ...}
    """
    collection = get_or_create_collection(book_id, chapter_name)

    question_embedding = embedding_model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=k,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    return [{"text": doc, "metadata": meta} for doc, meta in zip(documents, metadatas)]


def rerank_chunks(question: str, candidates: list, top_n: int = 3):
    """
    Stage 2 — slow, accurate reranking.
    Scores each (question, chunk) pair TOGETHER using a cross-encoder,
    rather than comparing precomputed independent vectors. Returns the
    top_n candidates sorted by that joint relevance score.

    candidates: list of dicts like {"text": ..., "metadata": ...}
    """
    if not candidates:
        return []

    pairs = [(question, c["text"]) for c in candidates]
    scores = reranker.predict(pairs)  # one float per pair, higher = more relevant

    scored = list(zip(candidates, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    return [c for c, score in scored[:top_n]]


def build_prompt(question: str, top_chunks: list) -> str:
    context_blocks = []
    for c in top_chunks:
        idx = c["metadata"]["chunk_index"]
        context_blocks.append(f"[Chunk {idx}]\n{c['text']}")
    context = "\n\n".join(context_blocks)

    return f"""You are a study assistant. Answer the following question based only on the provided context.
If the answer is not in the context, say so clearly. Do not generate structured notes — just answer directly and concisely.
When you use information from the context, cite it inline using its chunk number, e.g. [Chunk 3].

Context:
{context}

Question: {question}

Answer:"""

def ask_question(book_id: int, chapter_name: str, question: str, api_key: str) -> str:
    candidates = retrieve_candidates(book_id, chapter_name, question, k=10)
    top_chunks = rerank_chunks(question, candidates, top_n=3)

    if not top_chunks:
        return "I couldn't find relevant content for this question in the selected chapter."

    prompt = build_prompt(question, top_chunks)

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        reasoning_effort="none",
    )

    choice = response.choices[0] if response.choices else None
    content = choice.message.content if choice and choice.message else None
    answer = content or "The model returned an empty response."

    sources = [
        {
            "chunk_index": (c.get("metadata") or {}).get("chunk_index"),
            "chapter": (c.get("metadata") or {}).get("chapter"),
        }
        for c in top_chunks
    ]

    return answer + f"\n\nSources: {sources}"