# RAG Evaluation Methodology

This document outlines the metrics, evaluation algorithms, and golden dataset profiles used to measure answer quality.

## Evaluation Metrics

1. **Retrieval@5 (Recall)**:
   - Measures whether the hybrid retrieval system found the correct source files.
   - Calculated by finding the overlap percentage:
     $$Recall = \frac{|Retrieved \cap Expected|}{|Expected|}$$

2. **Faithfulness**:
   - Assesses whether the synthesized answer contains statements grounded strictly in retrieved sources (zero hallucination).
   - Approximated via semantic lexical analysis and critic validation checking.

3. **Answer Relevancy**:
   - Evaluates whether the generated answer corresponds closely to the user's query topic, checking keyword coverage.

4. **Citation Accuracy**:
   - Compares inline citations in the final text (e.g. `[1]`, `[2]`) to the actual index positions of the retrieved evidence chunks.

5. **Avg Latency**:
   - Records the total round-trip response execution time (in seconds).

---

## Golden Dataset Profile
The golden dataset `evals/questions.jsonl` contains **30 diverse questions** across various difficulties (Easy, Medium, Hard) and intents:
- **10 Document QA Questions**: Testing PDF/DOCX specs on autoscaling, metrics, database choices.
- **8 Codebase QA Questions**: Testing repository pathways, dependencies, entry points.
- **5 Architecture Summary Questions**: Testing structure and RAG dense/sparse reasoning.
- **4 Code Review Questions**: Reviewing modules, security validation flaws, and middleware.
- **3 Task Planning Questions**: Generating roadmap checklists and CI/CD upgrades.
