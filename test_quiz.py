import asyncio
import json

async def test_quiz_features():
    print("Testing Quiz API with Difficulty and Deduplication...")
    import sys
    import os
    sys.path.append(r"c:\neet prjct\backend")
    
    from app.services.quiz_service import generate_quiz
    
    # Test 1: Generate Easy Quiz
    print("\n--- Test 1: Easy Quiz (1 request) ---")
    try:
        q1 = await generate_quiz(
            subject="biology", 
            topic="cell organelle", 
            num_questions=1,
            difficulty="Easy",
            previous_questions=[]
        )
        for q in q1:
            print(f"Q: {q['question']}")
            print(f"Difficulty tag: {q.get('difficulty', 'MISSING')}")
            
        prev_questions = [q['question'] for q in q1]
        
        # Test 2: Generate Hard Quiz with Deduplication
        print("\n--- Test 2: Hard Quiz with Deduplication (1 request) ---")
        q2 = await generate_quiz(
            subject="biology", 
            topic="cell organelle", 
            num_questions=1,
            difficulty="Hard",
            previous_questions=prev_questions
        )
        
        repeated = 0
        for q in q2:
            print(f"Q: {q['question']}")
            print(f"Difficulty tag: {q.get('difficulty', 'MISSING')}")
            if q['question'] in prev_questions:
                print("❌ WARNING: Repeated question detected!")
                repeated += 1
                
        if repeated == 0:
            print("\n✅ Deduplication test passed! No repeated questions.")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    asyncio.run(test_quiz_features())
