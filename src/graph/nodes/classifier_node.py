# ==========================================
# File: src/graph/nodes/classifier_node.py
# ==========================================
import logging
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser

from src.core.llm_factory import LLMFactory
from src.domain.state import GraphState
from config.prompt_templates import CLASSIFIER_SYSTEM_PROMPT
from config.settings import settings

logger = logging.getLogger(settings.APP_NAME)

def classify_email(state: GraphState) -> GraphState:
    """
    Graph Node: Determines the intent of the user's email.
    
    Logic:
    1. Retrieve the full message history (Memory).
    2. Prepend the System Prompt.
    3. Invoke the LLM (Temperature=0 for strictness).
    4. Update state['intent'] with the result.
    """
    logger.info("--- NODE: Classifier ---")
    
    # 1. Get the model
    llm = LLMFactory.get_llm(temperature=0.0)
    
    # 2. Construct the prompt
    # We prepend the system instructions to the existing conversation history
    messages = [SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT)] + state["messages"]
    
    # 3. Invoke
    # StrOutputParser cleans up the result, ensuring we just get the string text
    chain = llm | StrOutputParser()
    response = chain.invoke(messages)
    
    # 4. Normalize Output
    intent = response.strip().upper()
    
    # Safety fallback if LLM hallucinates a new category
    valid_intents = {"UPDATE", "STATUS", "POLICY", "UNRELATED"}
    if intent not in valid_intents:
        logger.warning(f"LLM produced invalid intent '{intent}'. Defaulting to UNRELATED.")
        intent = "UNRELATED"
        
    logger.info(f"Classified intent as: {intent}")
    
    return {
        "intent": intent,
        "final_action": f"Classified as {intent}"
    }