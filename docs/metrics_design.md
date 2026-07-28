# RAG Sentinel – Metrics Design

## 1. Retrieval-Generation Alignment Score
- Measures how many retrieved documents are actually used in the answer
- High score = answer uses most relevant context
- Low score = answer ignores retrieved docs (dangerous!)

## 2. Citation Accuracy
- Verifies that citations actually exist in source documents
- Catches hallucinated citations

## 3. Context Contradiction
- Detects if answer contradicts its own sources
- Uses LLM-based comparison

## 4. Factual Consistency (Improved)
- Better than RAGAS faithfulness
- Compares answer against ALL retrieved docs

## 5. Confidence Calibration
- When system says 90% sure, is it actually right 90% of the time?