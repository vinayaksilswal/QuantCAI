import os
from typing import Annotated, Literal
from dotenv import load_dotenv
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Initialize Gemini
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def open_tool(tool_name: Literal["quantum-state", "circuit-builder"]) -> str:
    """
    Opens a specific quantum tool on the user's screen.
    
    Args:
        tool_name: The name of the tool to open. Options:
            - "quantum-state": Visualizer for single qubit states (Bloch sphere).
            - "circuit-builder": Tool for building and running quantum circuits.
    """
    return f"TOOL_OPEN:{tool_name}"

@tool
def manage_circuit(action: Literal["add_gate", "clear", "run"], params: dict = {}) -> str:
    """
    Performs an action on the active circuit builder.
    
    Args:
        action: The action to perform.
            - "add_gate": Add a gate. Params: {"gate": "H", "qubit": 0}
            - "clear": Clear the circuit.
            - "run": Run the circuit.
        params: Dictionary of parameters for the action.
    """
    import json
    return f"CIRCUIT_ACTION:{json.dumps({'action': action, 'params': params})}"

@tool
def explain_concept(concept: str) -> str:
    """
    Provides a deep explanation of a quantum concept.
    Use this when the user asks for a detailed explanation.
    """
    return f"EXPLAIN:{concept}"

tools = [open_tool, manage_circuit, explain_concept]

llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("chatbot_node", chatbot)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "chatbot_node")
builder.add_conditional_edges("chatbot_node", tools_condition)
builder.add_edge("tools", "chatbot_node")

graph = builder.compile()

# Example usage function for testing/CLI (optional)
def run_chat(message: str, history: list = []):
    state = {"messages": history + [{"role": "user", "content": message}]}
    output = graph.invoke(state)
    content = output["messages"][-1].content
    if isinstance(content, list):
        # Extract text from list of content blocks
        text_parts = [part["text"] for part in content if isinstance(part, dict) and "text" in part]
        return " ".join(text_parts)
    return str(content)

