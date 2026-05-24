# LangGraph Multi-Agent Design

This document describes the stateful execution model, node workflows, and critique loops of the multi-agent system built on **LangGraph**.

## Agent Stateful Schema

The orchestration engine stores execution values inside a shared state dictionary typed via `TypedDict`:
- `user_query`: Original input query.
- `intent`: Active query category (e.g. `document_qa`, `code_review`).
- `sub_questions`: Decomposed sub-questions.
- `selected_tools`: Activated search/action tools.
- `retrieved_contexts`: Raw dense/sparse RAG chunks.
- `graded_evidence`: Chunks passing grading filtration thresholds.
- `draft_answer`: Current LLM response draft.
- `citations`: Verified source matches.
- `critic_feedback`: Reject warnings or correction descriptions.
- `critic_attempts`: Number of self-correction loop revisions (max: 2).
- `thought_steps`: Visual reasoning trace steps displayed to the user.

---

## State Machine Nodes & Transitions

```
[START] -> query_router -> query_decomposer -> retriever_selector -> hybrid_retriever
            |
            v
[END] <- final_response <- critic (Approved)
                            |
                     (Re-evaluate) -> answer_generator <- evidence_grader
```

### Self-Correction & Critique Loop
One of the core features of the **Agentic Knowledge OS** is the **Critic self-correction loop**:
1. When the `answer_generator` node outputs an initial `draft_answer`, the state shifts to the `critic` node.
2. The `CriticAgent` parses the draft claims and matches them word-for-word against the `graded_evidence` chunks.
3. If the critic detects statement claims that are NOT backed by source materials, it sets `critic_feedback` to the detailed correction warning (e.g. *"Bị phát hiện bịa đặt số liệu trong mục autoscaling..."*) and routes the state back to `answer_generator`.
4. The `answer_generator` receives the feedback and rewrites the draft to comply.
5. To prevent infinite execution threads, the transition breaks after **2 attempts** and outputs the best compliance draft.
