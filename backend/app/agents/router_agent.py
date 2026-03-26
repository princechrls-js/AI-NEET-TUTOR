from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.agents.prompts import ROUTER_SYSTEM_PROMPT
from app.core.logger import get_logger
import re

logger = get_logger(__name__)

def detect_subject_keywords(question: str) -> str:
    """
    Rule-based subject detection as per Astra-Core rules.
    """
    q_lower = question.lower()
    
    bio_keywords = ["cell", "plant", "animal", "human physiology", "reproduction", "taxonomy", "ecology", "mitosis", "meiosis", "dna", "evolution", "biology"]
    chem_keywords = ["reaction", "compound", "bonding", "mole", "equilibrium", "organic", "inorganic", "chemistry", "acid", "base", "salt", "valence"]
    phys_keywords = ["force", "motion", "velocity", "acceleration", "energy", "work", "current", "optics", "physics", "optics", "quantum", "gravity", "mass"]
    graph_keywords = ["relationship", "connection", "link", "graph", "map", "connect", "between", "how is"]

    # Simple keyword match
    for k in bio_keywords:
        if k in q_lower: return "Astra-Bio"
    for k in chem_keywords:
        if k in q_lower: return "Astra-Chem"
    for k in phys_keywords:
        if k in q_lower: return "Astra-Phys"
    for k in graph_keywords:
        if k in q_lower: return "Astra-Graph"
        
    return None

async def route_question(question: str, ui_subject: str = None) -> str:
    """
    Astra-Core Router: Strictly uses ui_subject if provided. Falls back to keywords then LLM.
    """
    # 1. Strict UI Subject Binding
    if ui_subject:
        subject_map = {
            "biology": "Astra-Bio",
            "chemistry": "Astra-Chem",
            "physics": "Astra-Phys"
        }
        mapped = subject_map.get(ui_subject.lower())
        if mapped:
            logger.info(f"Astra-Core: Strictly binding to UI subject {mapped}.")
            return mapped

    # 2. Keyword check
    detected = detect_subject_keywords(question)
    if detected:
        logger.info(f"Astra-Core: Detected {detected} via keywords.")
        return detected

    # 2. LLM Fallback
    logger.info("Astra-Core: Falling back to LLM for subject detection.")
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTER_SYSTEM_PROMPT),
        ("human", "{question}")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({"question": question})
    agent_name = response.content.strip()
    
    # Filter only allowed names
    allowed = ["Astra-Bio", "Astra-Chem", "Astra-Phys", "Astra-Graph"]
    if agent_name in allowed:
        return agent_name
    
    # Default to Graph or General if unknown, but rules say pick one.
    return "Astra-Bio" # Default fallback
