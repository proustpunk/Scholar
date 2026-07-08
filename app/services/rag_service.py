from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from app.core.config import settings
import chromadb
from sentence_transformers import SentenceTransformer

# Keep existing embedding model for store_chunks
embedding_model_st = SentenceTransformer("all-MiniLM-L6-v2")

# LangChain embedding model for Q&A
lc_embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chromadb")

def get_or_create_collection(book_id: int, chapter_name: str):
    name = f"book_{book_id}_{chapter_name.replace(' ', '_').lower()}"
    return client.get_or_create_collection(name=name)

def store_chunks(book_id: int, chapter_name: str, chunks: list):
    """Embed and store chunks in ChromaDB."""
    collection = get_or_create_collection(book_id, chapter_name)
    embeddings = embedding_model_st.encode(chunks).tolist()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

def ask_question(book_id: int, chapter_name: str, question: str, api_key: str) -> str:
    """Full RAG pipeline using LangChain."""
    collection_name = f"book_{book_id}_{chapter_name.replace(' ', '_').lower()}"

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=lc_embedding_model,
        persist_directory="./chromadb"
    )

    llm = ChatGroq(
        api_key=api_key,
        model="openai/gpt-oss-20b"
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are a study assistant. Answer the question based only on the context below.
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {question}

Answer:"""
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa_chain.invoke({"query": question})
    return result["result"]