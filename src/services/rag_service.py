# ==========================================
# File: src/services/rag_service.py
# ==========================================
import logging
import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.vector_manager import vector_manager
from config.settings import settings

logger = logging.getLogger(settings.APP_NAME)

class RAGService:
    """
    Service responsible for Policy Retrieval and Knowledge Management.
    Used by the RAGExecutor node to fetch context for the Drafter.
    """

    def retrieve_policy_context(self, query: str, k: int = 3) -> str:
        """
        Retrieves the most relevant policy chunks for a given query.
        
        Args:
            query (str): The user's question (e.g., "What is the payment term?").
            k (int): Number of chunks to retrieve.
            
        Returns:
            str: A formatted string containing the retrieved context.
        """
        try:
            # 1. Get the retriever from our Singleton Manager
            retriever = vector_manager.get_retriever(k=k)
            
            # 2. Execute Search
            docs = retriever.invoke(query)
            
            if not docs:
                logger.info(f"RAG Search yielded no results for: '{query}'")
                return "No relevant policy documents found."

            # 3. Format Context for the LLM
            # We explicitly label excerpts to help the LLM cite sources if needed
            formatted_chunks = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content.replace("\n", " ").strip()
                source = doc.metadata.get("source", "Policy Doc")
                page = doc.metadata.get("page", "N/A")
                chunk_str = f"[Excerpt {i} from {source} (Page {page})]:\n{content}"
                formatted_chunks.append(chunk_str)

            result_str = "\n\n".join(formatted_chunks)
            logger.info(f"Retrieved {len(docs)} chunks for query: '{query}'")
            return result_str

        except RuntimeError as re:
            # Handles the case where the index is empty
            logger.warning(f"RAG Retrieval skipped: {re}")
            return "Policy index is currently empty. Cannot retrieve information."
        except Exception as e:
            logger.error(f"RAG Retrieval failed: {e}")
            return "Error retrieving policy information."

    def ingest_policy_file(self, file_path: str = None) -> str:
        """
        Admin Utility: Loads a PDF, splits it, and indexes it into FAISS.
        Defaults to the policy.pdf defined in settings.
        """
        target_path = file_path or str(settings.RAW_DATA_DIR / "policy.pdf")
        
        if not os.path.exists(target_path):
            return f"Error: Policy file not found at {target_path}"

        try:
            logger.info(f"Starting ingestion for: {target_path}")
            
            # 1. Load PDF
            loader = PyPDFLoader(target_path)
            docs = loader.load()
            
            # 2. Split Text (Optimized for Policy retrieval)
            # Policies usually have paragraphs; 1000 chars is a good balance.
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            
            # 3. Index via VectorManager
            vector_manager.add_documents(splits)
            
            return f"Successfully ingested {len(splits)} chunks from {Path(target_path).name}."

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return f"Ingestion failed: {str(e)}"

# Singleton Instance
rag_service = RAGService()