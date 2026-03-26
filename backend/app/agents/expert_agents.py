from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.agents.prompts import get_agent_prompt
from app.core.logger import get_logger

logger = get_logger(__name__)

async def get_expert_response(agent_name: str, question: str, context: str, history: list) -> str:
    """
    Invokes the specific expert agent (Bio, Chem, Phys, Graph).
    """
    logger.info(f"Expert Agent: invoking {agent_name}...")
    
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.2
    )

    prompt = get_agent_prompt(agent_name)
    chain = prompt | llm
    
    response = await chain.ainvoke({
        "question": question,
        "context": context,
        "history": history
    })
    
    return response.content
