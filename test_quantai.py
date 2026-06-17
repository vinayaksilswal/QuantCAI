import asyncio
import os
import sys
from dotenv import load_dotenv

# add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))


from backend.routers.quantai import llm_with_tools, TUTOR_AGENT_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

async def test():
    # Simulate a history where the AI returned a tool call
    messages = [
        SystemMessage(content=TUTOR_AGENT_PROMPT),
        HumanMessage(content="build bell state circuit"),
        AIMessage(content="", tool_calls=[{"name": "open_tool", "args": {"tool_name": "circuit-builder"}, "id": "call_123"}]),
        ToolMessage(content="Tool executed successfully by the client UI.", tool_call_id="call_123"),
        HumanMessage(content="build bell state circuit")
    ]
    import json
    try:
        async for chunk in llm_with_tools.astream(messages):
            content_text = ""
            if isinstance(chunk.content, list):
                for item in chunk.content:
                    if isinstance(item, dict) and "text" in item:
                        content_text += item["text"]
                    elif isinstance(item, str):
                        content_text += item
            elif isinstance(chunk.content, str):
                content_text = chunk.content

            if content_text:
                print(f"data: {json.dumps({'type': 'text', 'content': content_text})}\n\n")
                
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    print(f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': tc['args']})}\n\n")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"data: {json.dumps({'type': 'text', 'content': 'I encountered an issue generating a response.'})}\n\n")

asyncio.run(test())
