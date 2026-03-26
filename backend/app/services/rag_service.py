import json
from app.services.embedding_service import get_embedding
from app.services.vector_service import search_vector_store
from app.core.logger import get_logger
from app.schemas.db_schemas import ChatMessageCreate
from app.services.db_service import log_chat_interaction
import app.db.redis_client as redis_module
from fastapi.concurrency import run_in_threadpool
from app.agents.orchestrator import run_astra_agent, run_astra_agent_stream

logger = get_logger(__name__)

async def ask_question(subject: str, question: str, top_k: int = 5, user_id: str = "anonymous", conversation_history: list = None):
    """
    Orchestrates the RAG flow: Embed query -> Search -> Astra Multi-Agent Orchestrator.
    Uses Redis caching for the final result.
    """
    cache_key = f"qa:{subject}:{question.strip().lower()}"
    
    # Check cache
    if redis_module.redis_client:
        try:
            cached_data = await redis_module.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for question: {question}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")
            
    # 1. Embed question
    logger.info(f"Embedding question for {subject}")
    query_emb = await run_in_threadpool(get_embedding, question)
    
    # 2. Search Supabase PgVector
    logger.info(f"Searching pgvector for {subject}")
    retrieved_chunks = await run_in_threadpool(search_vector_store, subject, query_emb, top_k=top_k)
    
    # 3. Prepare Context
    context_text = ""
    citations = []
    
    if not retrieved_chunks:
        context_text = "No relevant documents found."
    else:
        for i, chunk in enumerate(retrieved_chunks):
            text_snippet = chunk.get("text", "")
            source_name = chunk.get("filename", "unknown source")
            
            context_text += f"\n--- Source {i+1}: {source_name} ---\n{text_snippet}\n"
            citations.append({
                "source_name": source_name,
                "chunk_index": i,
                "text_snippet": text_snippet[:50] + "..." # truncated
            })
    
    # 4. Generate Answer via Astra Multi-Agent System
    # Note: conversation_history from client is ignored in favor of persistent Redis memory
    logger.info(f"Invoking Astra Multi-Agent system for {user_id} with UI hint {subject}")
    # Isolate memory by subject
    session_id = f"{user_id}:{subject.lower()}"
    
    agent_result = await run_astra_agent(
        session_id=session_id,
        question=question,
        context=context_text,
        ui_subject=subject
    )
    
    answer = agent_result["answer"]
    agent_name = agent_result["agent"]
    difficulty = agent_result.get("difficulty", "Medium")
    
    # Log to Supabase
    chat_log = ChatMessageCreate(
        user_id=user_id,
        subject=subject,
        question=question,
        answer=answer
    )
    await run_in_threadpool(log_chat_interaction, chat_log)
    
    result = {
        "answer": answer,
        "citations": citations,
        "agent": agent_name,
        "difficulty": difficulty
    }
    
    # Save to Cache (24 hours expiry)
    if redis_module.redis_client:
        try:
            await redis_module.redis_client.setex(cache_key, 86400, json.dumps(result))
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")
            
    return result

async def ask_question_stream(subject: str, question: str, top_k: int = 5, user_id: str = "anonymous", conversation_history: list = None):
    """
    Orchestrates the RAG flow with Astra Multi-Agent streaming.
    """
    # 1. Embed question 
    query_emb = await run_in_threadpool(get_embedding, question)
    
    # 2. Search Supabase PgVector
    retrieved_chunks = await run_in_threadpool(search_vector_store, subject, query_emb, top_k=top_k)
    
    # 3. Prepare Context and Citations
    context_text = ""
    citations = []
    
    if not retrieved_chunks:
        context_text = "No relevant documents found."
    else:
        for i, chunk in enumerate(retrieved_chunks):
            text_snippet = chunk.get("text", "")
            source_name = chunk.get("filename", "unknown source")
            
            context_text += f"\n--- Source {i+1}: {source_name} ---\n{text_snippet}\n"
            citations.append({
                "source_name": source_name,
                "chunk_index": i,
                "text_snippet": text_snippet[:50] + "..." # truncated
            })
        
    # Yield citations as the first chunk
    yield json.dumps({"type": "citations", "data": citations})
    
    # 4. Generate Streaming Answer via Astra Multi-Agent System
    # Isolate memory by subject
    session_id = f"{user_id}:{subject.lower()}"
    
    full_answer = ""
    async for event in run_astra_agent_stream(
        session_id=session_id,
        question=question,
        context=context_text,
        ui_subject=subject
    ):
        yield event
        # Track full answer for logging
        data = json.loads(event)
        if data["type"] == "content":
            full_answer += data["data"]
        
    # 5. Background task: Log to Supabase
    try:
        chat_log = ChatMessageCreate(
            user_id=user_id,
            subject=subject,
            question=question,
            answer=full_answer
        )
        await run_in_threadpool(log_chat_interaction, chat_log)
    except Exception as e:
        logger.error(f"Failed to log stream interaction: {e}")
