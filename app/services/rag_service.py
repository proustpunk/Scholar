import chromadb
from sentence_transformers import SentenceTransformer
from app.services.llm_service import answer_question

client = chromadb.PersistentClient(path="./chromadb")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def get_or_create_collection(book_id: int, chapter_name: str):
    """Get or create a ChromaDB collection for a chapter."""
    name = f"book_{book_id}_{chapter_name.replace(' ', '_').lower()}"
    return client.get_or_create_collection(name=name)

def store_chunks(book_id: int, chapter_name: str, chunks: list):
    """Embed and store chunks in ChromaDB."""
    collection = get_or_create_collection(book_id, chapter_name)
    embeddings = embedding_model.encode(chunks).tolist()

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

def retrieve_context(book_id: int, chapter_name: str, question: str, top_k: int = 3) -> str:
    """Retrieve most relevant chunks for a question."""
    collection = get_or_create_collection(book_id, chapter_name)
    question_embedding = embedding_model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=top_k
    )

    chunks = results["documents"][0]
    return "\n\n".join(chunks)

def ask_question(book_id: int, chapter_name: str, question: str) -> str:
    """Full RAG pipeline — retrieve context then answer."""
    context = retrieve_context(book_id, chapter_name, question)
    return answer_question(question, context)