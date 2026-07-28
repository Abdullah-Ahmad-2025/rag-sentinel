import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.evaluators.alignment import RetrievalGenerationAlignmentEvaluator

def test_evaluator():
    # Example: A RAG system that ignores most retrieved docs
    query = "What is the capital of France?"

    retrieved_docs = [
        "Paris is the capital of France. It is located on the Seine River.",
        "France is a country in Western Europe with a population of 67 million.",
        "The Eiffel Tower is a famous landmark in Paris."
    ]

    # Bad answer: ignores the first doc (which has the specific answer)
    bad_answer = "France is a country in Europe with a population of 67 million."

    # Good answer: uses the first doc
    good_answer = "The capital of France is Paris, which is located on the Seine River."

    evaluator = RetrievalGenerationAlignmentEvaluator()

    print("=" * 60)
    print("EVALUATING BAD ANSWER (should score low)")
    print("=" * 60)
    result_bad = evaluator.evaluate(query, retrieved_docs, bad_answer)
    print(f"Alignment Score: {result_bad['alignment_score']:.2f}")
    print(f"Usage Map: {result_bad['usage_map']}")
    print(f"Explanation: {result_bad['explanation'][:200]}...")

    print("\n" + "=" * 60)
    print("EVALUATING GOOD ANSWER (should score high)")
    print("=" * 60)
    result_good = evaluator.evaluate(query, retrieved_docs, good_answer)
    print(f"Alignment Score: {result_good['alignment_score']:.2f}")
    print(f"Usage Map: {result_good['usage_map']}")
    print(f"Explanation: {result_good['explanation'][:200]}...")

if __name__ == "__main__":
    test_evaluator()