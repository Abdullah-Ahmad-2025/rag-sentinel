import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.evaluators.citation import CitationAccuracyEvaluator

def test_citation_evaluator():
    # Example: RAG answer with citations
    answer_with_valid_citations = """
    The capital of France is Paris [1]. 
    The Eiffel Tower is a famous landmark [2].
    """

    answer_with_invalid_citations = """
    The capital of France is Paris [5]. 
    France has a population of 67 million [10].
    """

    # Retrieved documents
    retrieved_docs = [
        "Paris is the capital of France. It is located on the Seine River.",
        "The Eiffel Tower is a famous landmark in Paris.",
        "France is a country in Western Europe with a population of 67 million."
    ]

    evaluator = CitationAccuracyEvaluator()

    print("=" * 60)
    print("EVALUATING ANSWER WITH VALID CITATIONS")
    print("=" * 60)
    result_valid = evaluator.evaluate(answer_with_valid_citations, retrieved_docs)
    print(f"Citation Accuracy: {result_valid['citation_accuracy']:.2f}")
    print(f"Valid: {result_valid['valid_citations']}/{result_valid['total_citations']}")
    print(f"Details: {result_valid['details']}")

    print("\n" + "=" * 60)
    print("EVALUATING ANSWER WITH INVALID CITATIONS")
    print("=" * 60)
    result_invalid = evaluator.evaluate(answer_with_invalid_citations, retrieved_docs)
    print(f"Citation Accuracy: {result_invalid['citation_accuracy']:.2f}")
    print(f"Valid: {result_invalid['valid_citations']}/{result_invalid['total_citations']}")
    print(f"Invalid Citations: {result_invalid['invalid_citations']}")

if __name__ == "__main__":
    test_citation_evaluator()