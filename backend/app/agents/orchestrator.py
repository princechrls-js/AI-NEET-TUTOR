from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.agents.router_agent import route_question
from app.agents.expert_agents import get_expert_response
from app.agents.memory import get_chat_history
from app.agents.prompts import get_agent_prompt
from app.core.logger import get_logger
import json

logger = get_logger(__name__)

async def classify_difficulty(question: str) -> str:
    """
    Classify question difficulty: Easy, Medium, Hard (NEET level).
    """
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0
    )
    
    prompt = f"Classify the difficulty of this NEET coaching question: '{question}'. Reply with ONLY one word: Easy, Medium, or Hard."
    response = await llm.ainvoke(prompt)
    diff = response.content.strip()
    return diff if diff in ["Easy", "Medium", "Hard"] else "Medium"

async def run_astra_agent(session_id: str, question: str, context: str, ui_subject: str = None):
    """
    Main Orchestrator for Astra Multi-Agent System (Unified).
    """
    # 1. Route
    agent_name = await route_question(question, ui_subject)
    logger.info(f"Orchestrator: Routing to {agent_name}")
    
    # 2. Difficulty Tagging
    difficulty = await classify_difficulty(question)
    logger.info(f"Orchestrator: Difficulty classified as {difficulty}")

    # 3. Memory
    memory = get_chat_history(session_id)
    history = memory.messages
    
    # 4. Expert response
    answer = await get_expert_response(agent_name, question, context, history)
    
    # 5. Save to Memory
    memory.add_user_message(question)
    memory.add_ai_message(answer)
    
    return {
        "agent": agent_name,
        "answer": answer,
        "difficulty": difficulty
    }

async def run_astra_agent_stream(session_id: str, question: str, context: str, ui_subject: str = None):
    """
    Streaming version of the orchestrator.
    Optimized for low latency: starts streaming answer immediately after routing.
    """
    import asyncio

    # 1. Route (Needed for agent prompt)
    agent_name = await route_question(question, ui_subject)
    logger.info(f"Orchestrator: Routing to {agent_name}")
    yield json.dumps({"type": "agent", "data": agent_name})

    # 2. Start Difficulty Classification in background (don't block the stream)
    diff_task = asyncio.create_task(classify_difficulty(question))

    # 3. Memory
    memory = get_chat_history(session_id)
    history = memory.messages
    
    # 4. Expert Streaming
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.2
    )
    
    prompt = get_agent_prompt(agent_name)
    chain = prompt | llm
    
    full_answer = ""
    async for chunk in chain.astream({
        "question": question,
        "context": context,
        "history": history
    }):
        if chunk.content:
            full_content = chunk.content
            full_answer += full_content
            yield json.dumps({"type": "content", "data": full_content})
            
    # 5. Yield Difficulty at the end (once it's ready)
    try:
        difficulty = await diff_task
    except Exception as e:
        logger.warning(f"Orchestrator: Difficulty classification failed: {e}")
        difficulty = "Medium"
    
    yield json.dumps({"type": "difficulty", "data": difficulty})

    # 6. Save to Memory
    memory.add_user_message(question)
    memory.add_ai_message(full_answer)
