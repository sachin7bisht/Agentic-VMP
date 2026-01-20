# ==========================================
# File: src/core/vector_manager.py
# ==========================================
import os
import shutil
from pathlib import Path
from typing import Optional, List
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.settings import settings

class VectorManager:
    """
    Singleton manager for the Vector Store (FAISS).
    Handles embedding model initialization and document indexing.
    """
    _instance: Optional["VectorManager"] = None
    _vectorstore: Optional[FAISS] = None
    _embeddings: Optional[Embeddings] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Internal init: Selects embedding model and loads the FAISS index if it exists.
        """
        print(f"[{settings.APP_NAME}] Initializing Vector Manager (FAISS)...")
        
        # 1. Load the appropriate Embedding Model
        self._embeddings = self._get_embedding_model()

        # 2. Check if FAISS index exists on disk
        index_path = Path(settings.VECTOR_STORE_PATH)
        if index_path.exists() and (index_path / "index.faiss").exists():
            print(f"[{settings.APP_NAME}] Loading existing FAISS index from: {index_path}")
            try:
                self._vectorstore = FAISS.load_local(
                    folder_path=str(index_path),
                    embeddings=self._embeddings,
                    allow_dangerous_deserialization=True # Safe because we created the index ourselves
                )
            except Exception as e:
                print(f"[{settings.APP_NAME}] Failed to load index: {e}. Starting fresh.")
                self._vectorstore = None
        else:
            print(f"[{settings.APP_NAME}] No existing index found. Starting fresh.")
            self._vectorstore = None

    def _get_embedding_model(self) -> Embeddings:
        """
        Factory method for Embedding Models based on config.
        """
        if settings.LLM_PROVIDER == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API Key required for OpenAI Embeddings")
            return OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL_NAME,
                openai_api_key=settings.OPENAI_API_KEY
            )
        
        elif settings.LLM_PROVIDER == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Google API Key required for Gemini Embeddings")
            return GoogleGenerativeAIEmbeddings(
                model="models/embedding-001", 
                google_api_key=settings.GOOGLE_API_KEY
            )
        
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")

    def get_retriever(self, k: int = 4):
        """
        Returns a retriever object for the RAG chain.
        """
        if not self._vectorstore:
            # If no docs are indexed yet, we can't create a retriever easily
            # We return a dummy empty retriever or raise an error based on preference
            print(f"[{settings.APP_NAME}] WARNING: Vector store is empty.")
            # Creating a dummy store just to return a valid retriever is a common pattern
            # but usually it's better to ensure data is loaded first.
            raise RuntimeError("Vector Store is empty. Please ingest documents first.")
            
        return self._vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k}
            # search_kwargs={"k": k, "score_threshold": settings.SIMILARITY_THRESHOLD}
        )

    def add_documents(self, documents: List[Document]):
        """
        Indexes new documents into FAISS and saves to disk.
        """
        if not documents:
            return

        print(f"Adding {len(documents)} documents to FAISS...")
        
        if self._vectorstore is None:
            # Create new index
            self._vectorstore = FAISS.from_documents(documents, self._embeddings)
        else:
            # Add to existing index
            self._vectorstore.add_documents(documents)
        
        # Explicitly save to disk for FAISS
        self._vectorstore.save_local(settings.VECTOR_STORE_PATH)
        print(f"FAISS index saved to {settings.VECTOR_STORE_PATH}")

    def reset(self):
        """
        DANGER: Clears the vector store.
        """
        if os.path.exists(settings.VECTOR_STORE_PATH):
            shutil.rmtree(settings.VECTOR_STORE_PATH)
            print("Deleted existing vector store on disk.")
            
        self._vectorstore = None
        self._initialize()

# Global Accessor
vector_manager = VectorManager()