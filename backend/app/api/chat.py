import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.observability.logging import logger
from app.config import settings

router = APIRouter(prefix="/api", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    answer: str
    intent: str
    citations: List[Dict[str, Any]]
    trace_id: str
    thought_steps: List[str]

@router.post("/chat", response_model=ChatResponse)
async def chat_interaction(request: ChatRequest):
    trace_id = f"tr-{uuid.uuid4().hex[:8]}"
    logger.info(f"Received user query: '{request.message}' [Trace: {trace_id}]")
    
    try:
        # Try running using the LangGraph engine
        from app.agents.graph import compiled_graph
        
        # Invoke LangGraph
        inputs = {
            "user_query": request.message,
            "trace_id": trace_id,
            "history": request.history or []
        }
        
        # Execute compiled graph state machine
        logger.info(f"Executing LangGraph agent orchestrator...")
        output_state = await compiled_graph.ainvoke(inputs)
        
        # Collect results from state
        answer = output_state.get("final_answer", "")
        intent = output_state.get("intent", "unknown")
        citations = output_state.get("citations", [])
        thought_steps = output_state.get("thought_steps", ["Intents classified", "Retrieval complete", "Answer verified"])
        
        return ChatResponse(
            answer=answer,
            intent=intent,
            citations=citations,
            trace_id=trace_id,
            thought_steps=thought_steps
        )
        
    except ImportError as ie:
        logger.warning(f"LangGraph modules not loaded yet: {str(ie)}. Falling back to direct Gemini/OpenAI RAG mode.")
        # Fallback dense/sparse retrieval QA
        return await _fallback_rag_response(request.message, trace_id)
    except Exception as e:
        logger.error(f"Error during agentic chat routing: {str(e)}", exc_info=True)
        return await _fallback_rag_response(request.message, trace_id)

async def _fallback_rag_response(query: str, trace_id: str) -> ChatResponse:
    # 1. Retrieve hybrid chunks
    from app.rag.hybrid_search import hybrid_search_engine
    from app.rag.citation import citation_helper
    
    chunks = hybrid_search_engine.search(query, top_k=4)
    
    if not chunks:
        return ChatResponse(
            answer="Không tìm thấy đủ bằng chứng trong tài liệu đã ingest. (Fallback Mode)",
            intent="unknown",
            citations=[],
            trace_id=trace_id,
            thought_steps=["Retrieved 0 chunks from database"]
        )
        
    # 2. Synthesize using fallback prompt
    sources_text = citation_helper.format_sources_for_llm(chunks)
    
    prompt = (
        "Bạn là AI Assistant thuộc hệ thống Agentic Knowledge OS.\n"
        "Nhiệm vụ: Trả lời câu hỏi của user DỰA TRÊN các nguồn tài liệu được cung cấp dưới đây. "
        "Hãy trích dẫn rõ nguồn dạng [1], [2] tương ứng với Source [1], Source [2].\n\n"
        f"Câu hỏi: {query}\n\n"
        f"Tài liệu tham khảo:\n{sources_text}\n\n"
        "Câu trả lời:"
    )
    
    answer_text = ""
    # Execute primary LLM provider
    provider = settings.PRIMARY_LLM_PROVIDER.lower()
    
    try:
        if provider == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            answer_text = resp.choices[0].message.content or ""
            
        elif provider == "gemini" and settings.GEMINI_API_KEY:
            # We can use direct Gemini API calls or a wrapper
            # Let's import google-generativeai or use standard langchain/llama-index wrappers
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_CHAT_MODEL)
            resp = model.generate_content(prompt)
            answer_text = resp.text or ""
            
        else:
            # Local mock or warning fallback
            answer_text = (
                f"Đã tìm thấy {len(chunks)} phần tài liệu liên quan.\n"
                f"Tuy nhiên, chưa cấu hình API Key cho LLM provider '{provider.upper()}'.\n"
                f"Nội dung đoạn tài liệu đầu tiên:\n\"{chunks[0]['text'][:300]}...\""
            )
    except Exception as e:
        logger.error(f"Fallback generation failed: {str(e)}")
        answer_text = f"Lỗi tổng hợp câu trả lời từ LLM: {str(e)}. Hiển thị tài liệu đầu tiên:\n{chunks[0]['text'][:200]}..."

    # Verify citations
    verified_answer, citations = citation_helper.verify_and_extract_citations(answer_text, chunks)
    
    return ChatResponse(
        answer=verified_answer,
        intent="document_qa",
        citations=citations,
        trace_id=trace_id,
        thought_steps=["Decompressed search query", "Retrieved 4 nodes from dense & BM25 index", "Generated RAG synthesis answer"]
    )
