# ==========================================
# File: src/services/data_loader.py
# ==========================================
import csv
import os
import shutil
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

from config.settings import settings
from config.logging_config import GLOBAL_LOGGER as logger
from src.core.db_manager import db_manager
from src.core.vector_manager import vector_manager

class DataLoader:
    """
    Handles ingestion of external data (CSV, PDF) into:
    1. SQL Database (Structured Facts: Vendors, Invoices)
    2. Vector Store (Unstructured Knowledge: Emails, Policies)
    """

    def ingest_all(self):
        """Orchestrates the full data loading process."""
        self._ensure_raw_data_exists()
        self._load_ledger_data()
        self._load_library_data()
        self._load_policy_data()

    def _ensure_raw_data_exists(self):
        """Checks if files are in the root and moves them to data/raw/."""
        os.makedirs(settings.RAW_DATA_DIR, exist_ok=True)
        
        files_to_move = ["ledger_data.csv", "library_data.csv", "policy.pdf"]
        for fname in files_to_move:
            if os.path.exists(fname):
                shutil.move(fname, str(settings.RAW_DATA_DIR / fname))
                logger.info("moved_file_to_raw", file=fname)

    def _load_ledger_data(self):
        """
        Reads ledger_data.csv and populates 'vendors' and 'invoices' tables.
        """
        csv_path = settings.RAW_DATA_DIR / "ledger_data.csv"
        if not csv_path.exists():
            logger.warning("ledger_data_not_found", path=str(csv_path))
            return

        logger.info("loading_ledger_data")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for row in reader:
                        # 1. Upsert Vendor
                        # We use INSERT OR IGNORE to handle duplicates based on EMAIL or Vendor_ID_STR
                        cursor.execute("""
                            INSERT OR IGNORE INTO vendors 
                            (vendor_id_str, name, contact_name, email, phone, address, category)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row['vendor_id'], 
                            row['company'], 
                            row['name'], 
                            row['email'], 
                            row['phone'], 
                            row['address'],
                            row['role'] # Using Role as Category
                        ))
                        
                        # 2. Get the internal SQL ID for this vendor
                        cursor.execute("SELECT id FROM vendors WHERE vendor_id_str = ?", (row['vendor_id'],))
                        vendor_row = cursor.fetchone()
                        
                        if vendor_row:
                            vendor_sql_id = vendor_row[0]
                            
                            # 3. Insert Invoice
                            cursor.execute("""
                                INSERT OR IGNORE INTO invoices 
                                (vendor_id, invoice_number, amount, status, issue_date, due_date)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                vendor_sql_id,
                                row['invoice_id'],
                                row['amount'],
                                row['status'],
                                row['invoice_date'],
                                row['due_date']
                            ))
                            
            logger.info("ledger_data_loaded_successfully")

        except Exception as e:
            logger.error("failed_loading_ledger", error=str(e))

    def _load_library_data(self):
        """
        Reads library_data.csv (Past Emails) and indexes them in Vector Store.
        """
        csv_path = settings.RAW_DATA_DIR / "library_data.csv"
        if not csv_path.exists():
            return

        logger.info("loading_library_data_rag")
        documents = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Construct a rich context string for RAG
                    content = (
                        f"Subject: {row['subject']}\n"
                        f"Item: {row['item_name']} ({row['category']})\n"
                        f"Summary: {row['summary']}\n"
                        f"Body: {row['body']}\n"
                        f"Reply: {row['reply_text']}"
                    )
                    
                    metadata = {
                        "source": "email_archive",
                        "vendor_id": row['vendor_id'],
                        "invoice_id": row['invoice_id'],
                        "category": row['category']
                    }
                    
                    documents.append(Document(page_content=content, metadata=metadata))
            
            if documents:
                vector_manager.add_documents(documents)
                logger.info("indexed_email_archive", count=len(documents))

        except Exception as e:
            logger.error("failed_loading_library", error=str(e))

    def _load_policy_data(self):
        """Loads policy.pdf into Vector Store."""
        pdf_path = settings.RAW_DATA_DIR / "policy.pdf"
        if not pdf_path.exists():
            return

        logger.info("loading_policy_pdf")
        try:
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            # Add metadata so we know this is policy, not email
            for d in docs:
                d.metadata["source"] = "policy_document"
                
            vector_manager.add_documents(docs)
            logger.info("indexed_policy_pdf", pages=len(docs))
        except Exception as e:
            logger.error("failed_loading_policy", error=str(e))

# Singleton
data_loader = DataLoader()