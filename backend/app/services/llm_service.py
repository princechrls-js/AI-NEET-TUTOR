from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

def get_llm() -> ChatOpenAI:
    """
    Returns a configured ChatOpenAI instance pointing to OpenRouter.
    """
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        logger.warning("No OPENROUTER_API_KEY provided. Model calls will fail unless mock_key is accepted.")

    return ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        temperature=0.3,
        api_key=api_key or "mock_key",
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": settings.APP_NAME
        }
    )

async def generate_answer(prompt: str) -> str:
    """
    Backward-compatible wrapper for services that still need a simple
    prompt-in, string-out async function (e.g. quiz_service).
    """
    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content
