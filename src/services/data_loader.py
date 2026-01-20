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
    Handles ingestion of external data (CSV, PDF) into SQL/Vector
    AND syncing SQL changes back to CSV.
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
        # Check root dir for files to move
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
                        cursor.execute("""
                            INSERT OR IGNORE INTO vendors 
                            (vendor_id_str, name, contact_name, email, phone, address, category)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row['vendor_id'], row['company'], row['name'], 
                            row['email'], row['phone'], row['address'], row['role']
                        ))
                        
                        # 2. Get ID
                        cursor.execute("SELECT id FROM vendors WHERE vendor_id_str = ?", (row['vendor_id'],))
                        vendor_row = cursor.fetchone()
                        
                        if vendor_row:
                            # 3. Insert Invoice
                            cursor.execute("""
                                INSERT OR IGNORE INTO invoices 
                                (vendor_id, invoice_number, amount, status, issue_date, due_date)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                vendor_row[0], row['invoice_id'], row['amount'], 
                                row['status'], row['invoice_date'], row['due_date']
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
        
        try:
            logger.info("loading_library_data_rag")
            documents = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    content = (f"Subject: {row['subject']}\nItem: {row['item_name']} ({row['category']})\n"
                               f"Summary: {row['summary']}\nBody: {row['body']}\nReply: {row['reply_text']}")
                    metadata = {"source": "email_archive", "vendor_id": row['vendor_id'], 
                                "invoice_id": row['invoice_id'], "category": row['category']}
                    documents.append(Document(page_content=content, metadata=metadata))
            if documents:
                vector_manager.add_documents(documents)
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
            for d in docs: 
                d.metadata["source"] = "policy_document"
            vector_manager.add_documents(docs)
            logger.info("indexed_policy_pdf", pages=len(docs))
        except Exception as e:
            logger.error("failed_loading_policy", error=str(e))

    def sync_db_to_csv(self):
        """
        Re-writes ledger_data.csv based on the current state of SQL Tables.
        Call this after any UPDATE operation.
        """
        csv_path = settings.RAW_DATA_DIR / "ledger_data.csv"
        logger.info("syncing_db_to_csv")
        
        query = """
            SELECT 
                v.vendor_id_str as vendor_id,
                v.contact_name as name,
                v.email,
                v.phone,
                v.address,
                v.name as company,
                v.category as role,
                i.invoice_number as invoice_id,
                i.amount,
                i.status,
                i.due_date,
                i.issue_date as invoice_date
            FROM vendors v
            JOIN invoices i ON v.id = i.vendor_id
        """
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                
                if rows:
                    # Get headers from cursor description
                    headers = [description[0] for description in cursor.description]
                    
                    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(rows)
                        
                    logger.info("csv_sync_complete", rows_written=len(rows))
                else:
                    logger.warning("csv_sync_skipped_empty_db")
                    
        except Exception as e:
            logger.error("failed_syncing_csv", error=str(e))

# Singleton
data_loader = DataLoader()