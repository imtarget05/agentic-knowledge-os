from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.router_agent import router_agent
from app.agents.document_qa_agent import document_qa_agent
from app.agents.codebase_agent import codebase_agent
from app.agents.task_planner_agent import task_planner_agent
from app.agents.critic_agent import critic_agent

from app.rag.hybrid_search import hybrid_search_engine
from app.tools.web_search import web_search_tool
from app.observability.logging import logger
from app.observability.tracing import tracer

# ----------------- Define Node Functions -----------------

async def query_router_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [query_router]")
    intent = await router_agent.classify_intent(state["user_query"])
    
    thought = f"Phân loại ý định người dùng (Intent Classification): '{intent}'"
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name="Router",
        step_name="query_classification",
        input_payload=state["user_query"],
        output_payload=intent
    )
    
    return {
        "intent": intent,
        "thought_steps": current_thoughts + [thought]
    }

async def query_decomposer_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [query_decomposer]")
    # Decompose queries if complex, otherwise pass query through
    sub_questions = [state["user_query"]]
    
    thought = f"Phân tách câu hỏi thành {len(sub_questions)} phần nhỏ để phân tích sâu."
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name="Planner",
        step_name="query_decomposition",
        input_payload=state["user_query"],
        output_payload=", ".join(sub_questions)
    )
    
    return {
        "sub_questions": sub_questions,
        "thought_steps": current_thoughts + [thought]
    }

async def retriever_selector_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [retriever_selector]")
    # Select retrieval strategies based on intent
    intent = state["intent"]
    selected_tools = ["hybrid_search"]
    
    if intent in ["codebase_qa", "architecture_summary", "code_review"]:
        selected_tools.append("codebase_retriever")
        
    thought = f"Lựa chọn phương thức tìm kiếm tối ưu: {', '.join(selected_tools)}"
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name="Router",
        step_name="retriever_selection",
        input_payload=intent,
        output_payload=", ".join(selected_tools)
    )
    
    return {
        "selected_tools": selected_tools,
        "thought_steps": current_thoughts + [thought]
    }

async def hybrid_retriever_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [hybrid_retriever]")
    query = state["user_query"]
    
    # Retrieve hybrid chunks
    chunks = hybrid_search_engine.search(query, top_k=6)
    
    thought = f"Thực hiện truy vấn hỗn hợp (Dense Vector + BM25 Keyword Search), tìm thấy {len(chunks)} đoạn thông tin liên quan."
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name="Retriever",
        step_name="hybrid_search",
        input_payload=query,
        output_payload=f"Retrieved {len(chunks)} chunks"
    )
    
    return {
        "retrieved_contexts": chunks,
        "thought_steps": current_thoughts + [thought]
    }

async def evidence_grader_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [evidence_grader]")
    retrieved = state.get("retrieved_contexts", [])
    
    # In a fully-fledged system, we would grade each chunk. 
    # For CRAG, we determine if we need a web fallback.
    graded = [c for c in retrieved if c.get("score", 0.0) >= 0.15]
    
    # If too few relevant chunks, trigger web search flag
    needs_web = len(graded) < 2
    
    thought = f"Đánh giá và chắt lọc tài liệu: Giữ lại {len(graded)}/{len(retrieved)} đoạn thông tin. "
    if needs_web:
        thought += "⚠️ Thông tin nội bộ không đủ, yêu cầu Web Search Fallback."
    else:
        thought += "Thông tin nội bộ đủ chất lượng."
        
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name="Grader",
        step_name="evidence_grading",
        input_payload=f"Inputs: {len(retrieved)}",
        output_payload=f"Graded: {len(graded)}, Needs Web: {needs_web}"
    )
    
    return {
        "graded_evidence": graded if graded else retrieved[:1],
        "needs_web_search": needs_web,
        "thought_steps": current_thoughts + [thought]
    }

async def web_search_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [web_search]")
    query = state["user_query"]
    web_results = await web_search_tool.search(query)
    
    existing_evidence = state.get("graded_evidence", [])
    
    thought = f"Bổ sung thông tin từ Web Search: Thu được thêm {len(web_results)} kết quả trực tuyến."
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name="WebSearch",
        step_name="tavily_fallback",
        input_payload=query,
        output_payload=f"Found {len(web_results)} results"
    )
    
    return {
        "graded_evidence": existing_evidence + web_results,
        "thought_steps": current_thoughts + [thought]
    }

async def answer_generator_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [answer_generator]")
    intent = state["intent"]
    query = state["user_query"]
    evidence = state.get("graded_evidence", [])
    
    draft_answer = ""
    citations = []
    
    # Delegate to the correct sub-agent based on classified intent
    if intent == "document_qa":
        draft_answer, citations = await document_qa_agent.answer_query(query, evidence)
        
    elif intent in ["codebase_qa", "architecture_summary", "code_review"]:
        draft_answer = await codebase_agent.process_codebase_query(query, evidence)
        # Parse citations out if any
        from app.rag.citation import citation_helper
        _, citations = citation_helper.verify_and_extract_citations(draft_answer, evidence)
        
    elif intent == "task_planning":
        draft_answer = await task_planner_agent.generate_tasks(query)
        citations = []
        
    else:
        draft_answer = "Tôi là trợ lý AI. Ý định câu hỏi chưa được phân loại chính xác, hiển thị dữ liệu tham khảo đầu tiên:\n"
        if evidence:
            draft_answer += f"\"{evidence[0]['text']}\""
        else:
            draft_answer += "Không có tài liệu nào liên quan."
            
    thought = f"Được xử lý bởi sub-agent '{intent.upper()}'. Đã soạn thảo câu trả lời nháp."
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name=intent.upper(),
        step_name="answer_generation",
        input_payload=query,
        output_payload=draft_answer
    )
    
    return {
        "draft_answer": draft_answer,
        "citations": citations,
        "thought_steps": current_thoughts + [thought]
    }

async def critic_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [critic]")
    query = state["user_query"]
    evidence = state.get("graded_evidence", [])
    draft = state["draft_answer"]
    attempts = state.get("critic_attempts", 0)
    
    passed, feedback = await critic_agent.evaluate_answer(query, evidence, draft)
    
    thought = f"Critic Agent kiểm định chất lượng: {'Đạt tiêu chuẩn ✅' if passed else 'Phát hiện lỗi cần điều chỉnh ❌'}"
    current_thoughts = state.get("thought_steps", []) or []
    
    tracer.trace_agent_step(
        trace_id=state["trace_id"],
        agent_name="Critic",
        step_name="quality_control",
        input_payload=draft,
        output_payload=f"Passed: {passed}, Feedback: {feedback}"
    )
    
    return {
        "critic_feedback": None if passed else feedback,
        "critic_attempts": attempts + 1,
        "thought_steps": current_thoughts + [thought]
    }

async def final_response_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: [final_response]")
    
    thought = "Hoàn thành tổng hợp câu trả lời và đóng gói trích dẫn nguồn."
    current_thoughts = state.get("thought_steps", []) or []
    
    return {
        "final_answer": state["draft_answer"],
        "thought_steps": current_thoughts + [thought]
    }

# ----------------- Conditional Routing -----------------

def route_after_grader(state: AgentState) -> str:
    if state.get("needs_web_search"):
        return "web_search"
    return "answer_generator"

def route_after_critic(state: AgentState) -> str:
    feedback = state.get("critic_feedback")
    attempts = state.get("critic_attempts", 0)
    
    if not feedback or attempts >= 2:
        return "approved"
    return "revise"

# ----------------- Build & Compile Graph -----------------

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("query_router", query_router_node)
workflow.add_node("query_decomposer", query_decomposer_node)
workflow.add_node("retriever_selector", retriever_selector_node)
workflow.add_node("hybrid_retriever", hybrid_retriever_node)
workflow.add_node("evidence_grader", evidence_grader_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("answer_generator", answer_generator_node)
workflow.add_node("critic", critic_node)
workflow.add_node("final_response", final_response_node)

# Set Entry Point
workflow.set_entry_point("query_router")

# Define Edges
workflow.add_edge("query_router", "query_decomposer")
workflow.add_edge("query_decomposer", "retriever_selector")
workflow.add_edge("retriever_selector", "hybrid_retriever")
workflow.add_edge("hybrid_retriever", "evidence_grader")

# CRAG Conditional Edge
workflow.add_conditional_edges(
    "evidence_grader",
    route_after_grader,
    {
        "web_search": "web_search",
        "answer_generator": "answer_generator"
    }
)

workflow.add_edge("web_search", "answer_generator")
workflow.add_edge("answer_generator", "critic")

workflow.add_conditional_edges(
    "critic",
    route_after_critic,
    {
        "approved": "final_response",
        "revise": "answer_generator"
    }
)

workflow.add_edge("final_response", END)

# Compile
compiled_graph = workflow.compile()
logger.info("LangGraph agent state machine (CRAG enabled) successfully compiled.")
