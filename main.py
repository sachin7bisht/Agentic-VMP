# ==========================================
# File: main.py
# ==========================================
import os
import sys
import logging
from typing import Dict, Any
from scripts.data_loader import data_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import settings
from config.logging_config import GLOBAL_LOGGER as logger
from src.graph.workflow import app
from src.domain.email_schemas import EmailInput
from src.core.db_manager import db_manager
from src.services.data_loader import data_loader # Import new loader

def bootstrap_system():
    """
    Initializes DB Schema and Ingests Data.
    """
    logger.info("system_startup_initiated")
    
    # 1. Initialize Database Schema
    db_path = settings.SQL_DB_PATH
    schema_path = settings.BASE_DIR / "data/sql/schema.sql"
    
    try:
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))

        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        with db_manager.get_connection() as conn:
            conn.executescript(schema_sql)
            
        logger.info("schema_applied_successfully")
        
    except Exception as e:
        logger.error("schema_init_failed", error=str(e))
        sys.exit(1)

    # 2. Ingest Data (CSV + PDF)
    # This handles Ledger (SQL) and Library/Policy (Vector)
    data_loader.ingest_all()

def run_agent_simulation(mock_email: Dict[str, Any]):
    # ... (Same as before) ...
    logger.info(f"\n{'='*50}\nSimulating Incoming Email...\n{'='*50}")
    
    try:
        email_obj = EmailInput(**mock_email)
    except Exception as e:
        logger.error("Invalid email input", error=str(e))
        return

    initial_state = {
        "email_input": email_obj,
        "messages": [],
        "trials": 0
    }

    try:
        output = app.invoke(initial_state)
        print(f"\n{'='*50}\nFINAL OUTPUT\n{'='*50}")
        print(f"INTENT: {output.get('intent')}")
        print("-" * 20)
        print("GENERATED EMAIL:")
        print(output.get("generated_email"))
        print(f"{'='*50}\n")
        
    except Exception as e:
        logger.error("Workflow execution failed", error=str(e))

if __name__ == "__main__":
    # 1. Bootstrap
    bootstrap_system()
    
    # 2. Test Scenario (Using data from your CSV)
    # Testing with 'Aaron Roberts' from ledger_data.csv
    test_email = {
        "id": "msg_test_01",
        "thread_id": "thread_demo_01",
        "message_id": "msg_head_01",
        "sender": "jchavez@gmail.com",  # From ledger_data.csv (V7755)
        "subject": "Invoice Inquiry",
        "body": "Hi, give me important policy terms."
    }
    
    # 3. Run
    run_agent_simulation(test_email)