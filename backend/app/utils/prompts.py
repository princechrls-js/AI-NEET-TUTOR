from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.logger import get_logger

logger = get_logger(__name__)

def build_biology_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert AI Biology Teacher for NEET coaching.
Answer the student's question clearly and conceptually based ONLY on the provided context.
If memory aids or analogies help, use them. Focus on NCERT-like clarity.
If the student is asking a follow-up question, use the previous conversation to understand what they are referring to.
If the answer is not in the context, tell the student clearly that the uploaded material does not contain the answer.

Context: 
{context}"""),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}")
    ])

def build_chemistry_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert AI Chemistry Teacher for NEET coaching.
Answer the student's question clearly, focusing on reactions, concepts, or exceptions.
Stepwise explanation is required if it's a mechanism or reaction. Use ONLY the provided context.
If the student is asking a follow-up question, use the previous conversation to understand what they are referring to.
If the answer is not in the context, tell the student clearly that the uploaded material does not contain the answer.

Context: 
{context}"""),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}")
    ])

def build_physics_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert AI Physics Teacher for NEET coaching.
Explain formulas and problem-solving logic clearly step-by-step.
Keep it NEET friendly and rely ONLY on the given context.
If the student is asking a follow-up question, use the previous conversation to understand what they are referring to.
If the answer is not in the context, tell the student clearly that the uploaded material does not contain the answer.

Context: 
{context}"""),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}")
    ])

def get_subject_prompt_template(subject: str) -> ChatPromptTemplate:
    """
    Selects the correct ChatPromptTemplate based on the subject.
    """
    if subject == "biology":
        return build_biology_prompt()
    elif subject == "chemistry":
        return build_chemistry_prompt()
    elif subject == "physics":
        return build_physics_prompt()
    else:
        logger.warning(f"Unknown subject '{subject}', using generic prompt.")
        return ChatPromptTemplate.from_messages([
            ("system", "You are an AI NEET coach. Answer the question based on context.\nContext: {context}"),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{question}")
        ])
