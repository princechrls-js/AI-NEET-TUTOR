import json
import re
from app.services.embedding_service import get_embedding
from app.services.vector_service import search_vector_store
from app.services.llm_service import generate_answer
from app.utils.quiz_prompts import get_quiz_prompt
from app.core.logger import get_logger
import asyncio

logger = get_logger(__name__)


def _extract_json_array(text: str) -> list:
    """
    Robustly extracts a JSON array from LLM output, handling
    markdown code blocks, extra text, and partially truncated JSON.
    """
    # Try to find JSON in markdown code blocks first
    code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find a raw JSON array
    array_match = re.search(r'\[.*\]', text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    # If the JSON is truncated (common with large question counts),
    # try to repair it by finding the last complete object
    array_start = text.find('[')
    if array_start != -1:
        raw = text[array_start:]
        # Find all complete question objects by looking for closing braces
        # that are followed by comma or end bracket
        last_complete = raw.rfind('}')
        if last_complete != -1:
            attempt = raw[:last_complete + 1]
            # Ensure it ends properly as a JSON array
            if not attempt.rstrip().endswith(']'):
                attempt = attempt.rstrip().rstrip(',') + ']'
            try:
                result = json.loads(attempt)
                logger.info(f"Recovered {len(result)} questions from truncated JSON")
                return result
            except json.JSONDecodeError:
                pass

    # Last resort: try to parse individual question objects
    objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    questions = []
    for obj_str in objects:
        try:
            obj = json.loads(obj_str)
            if 'question' in obj and 'options' in obj:
                questions.append(obj)
        except json.JSONDecodeError:
            continue
    
    if questions:
        logger.info(f"Recovered {len(questions)} questions via individual object parsing")
        return questions

    raise json.JSONDecodeError("Could not extract any valid quiz JSON", text, 0)


async def _generate_batch(subject: str, topic: str, context_text: str, num_questions: int, difficulty: str, previous_questions: list[str]) -> list:
    """Generate a single batch of quiz questions."""
    prompt = get_quiz_prompt(subject, topic, context_text, num_questions, difficulty, previous_questions)
    raw_answer = await generate_answer(prompt)
    return _extract_json_array(raw_answer)


async def generate_quiz(subject: str, topic: str, num_questions: int = 5, top_k: int = 8, difficulty: str = "Medium", previous_questions: list[str] = None) -> list:
    """
    Orchestrates quiz generation with batching for large question counts.
    Splits into batches of 10 to avoid LLM token limit issues.
    """
    logger.info(f"Generating quiz for {subject}/{topic} ({num_questions} questions, {difficulty} difficulty)")
    query_emb = get_embedding(topic)

    # Use more chunks for larger quizzes
    effective_top_k = min(top_k + (num_questions // 10), 15)
    retrieved_chunks = search_vector_store(subject, query_emb, top_k=effective_top_k)

    if not retrieved_chunks:
        logger.warning(f"No context found for quiz on {subject}/{topic}")
        raise ValueError(f"No content found for topic '{topic}' in {subject}. Please ingest relevant PDFs first.")

    # Build context
    context_text = ""
    for i, chunk in enumerate(retrieved_chunks):
        text_snippet = chunk.get("text", "")
        source_name = chunk.get("filename", "unknown")
        context_text += f"\n--- Source {i+1}: {source_name} ---\n{text_snippet}\n"

    # Split into batches of 10 questions max per LLM call
    BATCH_SIZE = 10
    tasks = []
    remaining = num_questions
    batch_num = 0
    
    current_exclusions = list(previous_questions) if previous_questions else []

    while remaining > 0:
        batch_count = min(remaining, BATCH_SIZE)
        tasks.append(_generate_batch(subject, topic, context_text, batch_count, difficulty, current_exclusions))
        remaining -= batch_count

    logger.info(f"Executing {len(tasks)} batches concurrently for {num_questions} questions")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_questions = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Batch failed: {r}")
        elif isinstance(r, list):
            for q in r:
                # Deduplicate loosely by checking if question text is already in list
                if not any(existing['question'] == q['question'] for existing in all_questions):
                    q['question_number'] = len(all_questions) + 1
                    all_questions.append(q)

    # If we didn't hit our target due to errors or dupes, we might be slightly short, but that's fine.
    if not all_questions:
        raise ValueError("No questions could be generated. Try a different topic.")

    logger.info(f"Successfully generated {len(all_questions)} total quiz questions")
    return all_questions
