import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.evaluators.citation import CitationAccuracyEvaluator


def test_citation_evaluator():
    retrieved_docs = [
        "Paris is the capital of France. It is located on the Seine River.",
        "The Eiffel Tower is a famous landmark in Paris.",
        "France is a country in Western Europe with a population of 67 million.",
    ]

    answer_valid = (
        "Paris is the capital of France [1]. "
        "The Eiffel Tower is a famous landmark in Paris [2]."
    )
    answer_invalid = (
        "The moon is made of cheese [1]. "
        "France has a population of 67 million [10]."
    )

    evaluator = CitationAccuracyEvaluator()

    print("=" * 60)
    print("EVALUATING ANSWER WITH VALID CITATIONS")
    print("=" * 60)
    result_valid = evaluator.evaluate(answer_valid, retrieved_docs)
    print(f"Citation Accuracy: {result_valid['citation_accuracy']:.2f}")
    print(f"Valid: {result_valid['valid_citations']}/{result_valid['total_citations']}")
    for detail in result_valid['details']:
        print(f"  {detail}")

    print("\n" + "=" * 60)
    print("EVALUATING ANSWER WITH INVALID CITATIONS")
    print("=" * 60)
    result_invalid = evaluator.evaluate(answer_invalid, retrieved_docs)
    print(f"Citation Accuracy: {result_invalid['citation_accuracy']:.2f}")
    print(f"Valid: {result_invalid['valid_citations']}/{result_invalid['total_citations']}")
    for detail in result_invalid['details']:
        print(f"  {detail}")


if __name__ == "__main__":
    test_citation_evaluator()
