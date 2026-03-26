import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(r"c:\neet prjct\backend")
load_dotenv(r"c:\neet prjct\backend\.env")

from app.services.quiz_service import generate_quiz
import app.db.redis_client as redis_client

async def debug_quiz():
    print("Testing animal kingdom biology quiz generation...")
    await redis_client.init_redis()
    
    try:
        q = await generate_quiz(
            subject="biology",
            topic="animal kingdom",
            num_questions=25,
            difficulty="Hard",
            previous_questions=[]
        )
        print(f"Success! Generated {len(q)} questions.")
        for item in q[:3]:
           print("- ", item['question'])
    except Exception as e:
        print(f"DEBUG ERROR CAUGHT: {type(e).__name__} - {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(debug_quiz())
