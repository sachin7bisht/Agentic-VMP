# ==========================================
# File: src/web/server.py
# ==========================================
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sys
import os

# Ensure root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.graph.workflow import app as agent_app
from src.domain.email_schemas import EmailInput
from config.logging_config import GLOBAL_LOGGER as logger
from config.settings import settings
from src.core.db_manager import db_manager
from src.services.data_loader import data_loader

# Initialize FastAPI
app = FastAPI(title="Agentia Vendor Portal")

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    """
    Ensures the DB is initialized and CSV data is loaded when the server starts.
    """
    logger.info("web_server_startup_initiated")
    
    # 1. Initialize Schema
    schema_path = settings.BASE_DIR / "data/sql/schema.sql"
    try:
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        with db_manager.get_connection() as conn:
            conn.executescript(schema_sql)
        logger.info("schema_verified")
    except Exception as e:
        logger.error("schema_load_failed", error=str(e))

    # 2. Ingest CSV Data
    data_loader.ingest_all()
    logger.info("data_ingestion_complete")

class ChatRequest(BaseModel):
    sender: str
    thread_id: str
    message: str

@app.get("/")
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    """
    API Endpoint called by script.js.
    """
    log = logger.bind(endpoint="/chat", thread_id=payload.thread_id)
    log.info("received_web_message", sender=payload.sender)

    # 1. Map Web Input to Agent Input
    agent_input = EmailInput(
        id=f"web_{payload.thread_id}",
        thread_id=payload.thread_id,
        message_id="web_msg",
        references="",
        sender=payload.sender,
        subject="Web Chat Inquiry",
        body=payload.message
    )

    initial_state = {
        "email_input": agent_input,
        "messages": [], # MemoryNode will handle history loading
        "trials": 0
    }

    try:
        # 2. Invoke Graph
        output = await agent_app.ainvoke(initial_state)
        response_text = output.get("generated_email", "No response generated.")
        
        # Cleanup: Remove standard email signature for a better chat experience
        response_text = response_text.replace("Best regards,\nAgentia Vendor Team", "")
        
        return {"response": response_text.strip()}

    except Exception as e:
        log.error("web_chat_error", error=str(e))
        return {"response": "System Error: Please check the logs."}

if __name__ == "__main__":
    print("Starting Web Server at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)