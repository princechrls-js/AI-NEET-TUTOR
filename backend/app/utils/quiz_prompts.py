from app.core.logger import get_logger

logger = get_logger(__name__)


def get_quiz_prompt(subject: str, topic: str, context: str, num_questions: int = 5, difficulty: str = "Medium", previous_questions: list[str] = None) -> str:
    """
    Generates a structured prompt that asks the LLM to produce NEET-style MCQs
    in strict JSON format based on the provided context.
    """
    subject_style = {
        "biology": "Focus on conceptual understanding, NCERT-based facts, and diagram-related reasoning.",
        "chemistry": "Include reaction-based, exception-based, and conceptual MCQs. Cover both organic and inorganic if relevant.",
        "physics": "Include formula-based, numerical, and conceptual MCQs. Show key formulas in options where applicable."
    }

    style_hint = subject_style.get(subject, "Focus on NEET-level difficulty and conceptual clarity.")
    
    difficulty_hint = ""
    if difficulty.lower() == "easy":
        difficulty_hint = "Make the questions straightforward, focusing on basic recall and direct application of formulas/concepts."
    elif difficulty.lower() == "hard":
        difficulty_hint = "Make the questions challenging, requiring multi-step reasoning, deep conceptual understanding, or identifying exceptions/edge cases."
    else:
        difficulty_hint = "Make the questions moderately challenging, representing standard NEET questions."

    avoid_questions_hint = ""
    if previous_questions and len(previous_questions) > 0:
        avoid_questions_hint = "\nCRITICAL: DO NOT generate any questions that are exactly identical or extremely similar to the following previously generated questions:\n"
        for q in previous_questions:
            avoid_questions_hint += f"- {q}\n"

    return f"""You are an expert NEET {subject.capitalize()} question paper setter.

Generate exactly {num_questions} NEET-style Multiple Choice Questions (MCQs) on the topic "{topic}" using ONLY the context provided below.

Rules:
1. Each question must have exactly 4 options labeled A, B, C, D.
2. Exactly one option must be correct.
3. Include a brief explanation for the correct answer.
4. Questions should match NEET difficulty level. Set the difficulty to {difficulty}. {difficulty_hint}
5. {style_hint}{avoid_questions_hint}

Context:
{context}

IMPORTANT: You MUST respond with ONLY a valid JSON array, no extra text before or after. Use this exact format:
[
  {{
    "question_number": 1,
    "question": "What is ...?",
    "options": [
      {{"label": "A", "text": "Option A text"}},
      {{"label": "B", "text": "Option B text"}},
      {{"label": "C", "text": "Option C text"}},
      {{"label": "D", "text": "Option D text"}}
    ],
    "correct_answer": "A",
    "explanation": "Brief explanation of why A is correct.",
    "difficulty": "{difficulty}"
  }}
]

Generate {num_questions} questions now:"""
