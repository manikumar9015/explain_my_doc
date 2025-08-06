# backend/vector_store/chroma.py

import chromadb
import uuid

class ChromaStore:
    def __init__(self, path: str = "./chroma_db"):
        print("Initializing ChromaDB Client...")
        self.client = chromadb.PersistentClient(path=path)
        print("ChromaDB Client initialized.")

    def create_collection(self) -> str:
        """Creates a new unique collection and returns its name (session ID)."""
        session_id = str(uuid.uuid4())
        self.client.get_or_create_collection(name=session_id)
        print(f"Created new collection with name: {session_id}")
        return session_id

    def delete_collection(self, collection_name: str):
        """Deletes a collection by its name."""
        self.client.delete_collection(name=collection_name)
        print(f"Deleted collection: {collection_name}")

    def add_documents(self, collection_name: str, chunks: list[str], embeddings: list[list[float]], metadatas: list[dict]):
        """Adds documents to a specific named collection."""
        if not chunks:
            return
        collection = self.client.get_collection(name=collection_name)
        ids = [str(uuid.uuid4()) for _ in chunks]
        collection.add(embeddings=embeddings, documents=chunks, metadatas=metadatas, ids=ids)
        print(f"Added {len(chunks)} documents to collection '{collection_name}'.")

    def query(self, collection_name: str, query_embedding: list[float], n_results: int = 5) -> list[str]:
        """Queries a specific named collection."""
        collection = self.client.get_collection(name=collection_name)
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        return results['documents'][0]

vector_store_instance = ChromaStore()