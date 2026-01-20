# ==========================================
# File: src/graph/workflow.py
# ==========================================
from langgraph.graph import StateGraph, START, END

# Import Domain
from src.domain.state import GraphState

# Import Nodes
from src.graph.nodes.security_node import security_check
from src.graph.nodes.memory_node import load_memory
from src.graph.nodes.classifier_node import classify_email
from src.graph.nodes.executor_nodes import execute_status, execute_update, execute_policy
from src.graph.nodes.drafter_node import draft_response, rejection_response
from src.graph.nodes.save_node import save_conversation

# Import Edges
from src.graph.edges import route_security, route_intent

def build_workflow():
    """
    Constructs the compiled Graph Application.
    """
    # 1. Initialize Graph
    workflow = StateGraph(GraphState)

    # 2. Add Nodes
    workflow.add_node("security_check", security_check)
    workflow.add_node("load_memory", load_memory)
    workflow.add_node("classify_email", classify_email)
    
    # Executors
    workflow.add_node("execute_status", execute_status)
    workflow.add_node("execute_update", execute_update)
    workflow.add_node("execute_policy", execute_policy)
    
    # Response Generators
    workflow.add_node("draft_response", draft_response)
    workflow.add_node("rejection_response", rejection_response)
    
    # Finalizer
    workflow.add_node("save_conversation", save_conversation)

    # 3. Define Flow (Edges)
    
    # Start -> Security
    workflow.add_edge(START, "security_check")
    
    # Security -> (Memory OR Rejection)
    workflow.add_conditional_edges(
        "security_check",
        route_security
    )
    
    # Memory -> Classifier
    workflow.add_edge("load_memory", "classify_email")
    
    # Classifier -> (Status OR Update OR Policy OR Drafter)
    workflow.add_conditional_edges(
        "classify_email",
        route_intent
    )
    
    # Executors -> Drafter
    # All branches converge here to format the final email
    workflow.add_edge("execute_status", "draft_response")
    workflow.add_edge("execute_update", "draft_response")
    workflow.add_edge("execute_policy", "draft_response")
    
    # Drafter -> Save
    workflow.add_edge("draft_response", "save_conversation")
    
    # Rejection -> Save (We still want to log the attempt)
    workflow.add_edge("rejection_response", "save_conversation")
    
    # Save -> End
    workflow.add_edge("save_conversation", END)

    # 4. Compile
    return workflow.compile()

# Expose the runnable app
app = build_workflow()