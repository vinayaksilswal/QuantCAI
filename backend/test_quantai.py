import asyncio
import os
from QuantAI import run_chat_stream
from dotenv import load_dotenv

load_dotenv()

async def test_chat():
    print("Starting chat test...")
    try:
        async for chunk in run_chat_stream("Hello, who are you?"):
            print(f"Chunk: {chunk}")
    except Exception as e:
        print(f"Error during chat: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())
