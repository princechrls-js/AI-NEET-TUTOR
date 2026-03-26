import asyncio
import sys
from dotenv import load_dotenv

sys.path.append(r"c:\neet prjct\backend")
load_dotenv(r"c:\neet prjct\backend\.env")

from app.services.rag_service import ask_question
import app.db.redis_client as redis_client

async def test_memory():
    print("Testing chat memory...")
    await redis_client.init_redis()
    
    history = [
        {"role": "user", "content": "What is taxonomy?"},
        {"role": "assistant", "content": "Taxonomy is the science of classification."}
    ]
    
    try:
        # Ask a follow-up question
        res = await ask_question(
            subject="biology",
            question="Who is considered the father of it?",
            top_k=3,
            conversation_history=history
        )
        print("Response received!")
        print(res["answer"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_memory())
