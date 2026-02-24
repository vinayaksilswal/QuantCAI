import os
import json
import logging
from typing import Annotated, Literal
from dotenv import load_dotenv
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def open_tool(tool_name: Literal["quantum-states", "circuit-builder"]) -> str:
    """
    Opens a specific quantum tool on the user's screen.
    
    Args:
        tool_name: The name of the tool to open. Options:
            - "quantum-states": Visualizer for single qubit states (Bloch sphere).
            - "circuit-builder": Tool for building and running quantum circuits.
    """
    return f"TOOL_OPEN:{tool_name}"

@tool
def apply_gate_to_visualizer(gate: Literal["H", "X", "Y", "Z", "S", "T"]) -> str:
    """
    Applies a quantum gate to the single-qubit visualizer tool.
    Use this when the user is on the Quantum States page or wants to see a state change.
    """
    return f"VISUALIZER_GATE:{gate}"

@tool
def manage_circuit(action: Literal["add_gate", "clear", "run"], params: dict = {}) -> str:
    """
    Performs an action on the active circuit builder.
    
    Args:
        action: The action to perform.
            - "add_gate": Add a gate. Params: {"gate": "H", "qubit": 0}. 
              For multi-qubit gates like CNOT, use {"gate": "CX", "control": 0, "target": 1}.
            - "clear": Clear the circuit.
            - "run": Run the circuit.
        params: Dictionary of parameters for the action.
    """
    return f"CIRCUIT_ACTION:{json.dumps({'action': action, 'params': params})}"

@tool
def explain_concept(concept: str) -> str:
    """
    Provides a deep explanation of a quantum concept.
    Use this when the user asks for a detailed explanation.
    """
    return f"EXPLAIN:{concept}"

@tool
def navigate_to_learn(section: str = None) -> str:
    """
    Navigates the user to the Learn page.
    
    Args:
        section: Optional section of the learn page to scroll to (e.g., "qubits", "applications").
    """
    return f"NAVIGATE:learn{f'#{section}' if section else ''}"

@tool
def start_tutorial(tutorial_id: str) -> str:
    """
    Starts a specific interactive quantum tutorial.
    
    Args:
        tutorial_id: The ID of the tutorial to start. Options:
            - "bell-state": Create a Bell State.
            - "teleportation": Quantum Teleportation.
    """
    return f"START_TUTORIAL:{tutorial_id}"

tools = [open_tool, manage_circuit, explain_concept, navigate_to_learn, start_tutorial, apply_gate_to_visualizer]

if llm:
    llm_with_tools = llm.bind_tools(tools)
else:
    llm_with_tools = None

async def chatbot(state: State):
    if not llm_with_tools:
        return {"messages": [{"role": "ai", "content": "I'm sorry, my AI brain (Google API) is not initialized. Please check the backend configuration."}]}
    
    try:
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
        error_msg = "I'm sorry, I'm having trouble connecting to my AI brain. Please try again in a moment."
        if "API_KEY_INVALID" in str(e):
            error_msg = "I'm sorry, the Google API key provided is invalid. Please check the backend configuration."
        
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=error_msg)]}

builder = StateGraph(State)
builder.add_node("chatbot_node", chatbot)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "chatbot_node")
builder.add_conditional_edges("chatbot_node", tools_condition)
builder.add_edge("tools", "chatbot_node")

graph = builder.compile()

async def run_chat_stream(message: str, history: list = []):
    """
    Runs the chatbot and yields events in a format suitable for Server-Sent Events.
    """
    state = {"messages": history + [{"role": "user", "content": message}]}
    
    sent_text = ""
    sent_tool_calls_ids = set()

    try:
        async for event in graph.astream(state, stream_mode="values"):
            if not event or "messages" not in event:
                continue
                
            last_message = event["messages"][-1]
            if last_message.type != "ai":
                continue

            # Text Content
            if last_message.content:
                full_content = ""
                if isinstance(last_message.content, list):
                    full_content = "".join([part["text"] for part in last_message.content if isinstance(part, dict) and "text" in part])
                else:
                    full_content = str(last_message.content)
                
                if len(full_content) > len(sent_text):
                    new_part = full_content[len(sent_text):]
                    yield f"data: {json.dumps({'type': 'text', 'content': new_part})}\n\n"
                    sent_text = full_content
            
            # Tool Calls
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                for tc in last_message.tool_calls:
                    tc_id = tc.get("id")
                    if tc_id and tc_id not in sent_tool_calls_ids:
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': tc['args']})}\n\n"
                        sent_tool_calls_ids.add(tc_id)
    except Exception as e:
        logger.error(f"Error in run_chat_stream: {str(e)}")
        yield f"data: {json.dumps({'type': 'text', 'content': 'I encountered an error while thinking. Please try again.'})}\n\n"

def run_chat(message: str, history: list = []):
    """Legacy sync function for chat (not used for streaming)."""
    state = {"messages": history + [{"role": "user", "content": message}]}
    output = graph.invoke(state)
    return output["messages"][-1].content
