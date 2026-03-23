import chromadb
import os
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

load_dotenv()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../data/chromadb")
client = chromadb.PersistentClient(path=CHROMA_PATH)

ef = DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="maintenance_logs",
    embedding_function=ef
)

def add_to_vector_store(text: str, source: str):
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    ids = [f"{source}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source} for _ in chunks]
    collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
    print(f"Added {len(chunks)} chunks from {source}")

def search_vector_store(query: str, n_results: int = 5):
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []