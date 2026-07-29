import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.evaluators.contradiction import ContextContradictionDetector

def test_contradiction():
    # Example: Answer that contradicts retrieved docs
    query = "What color is the sky?"

    retrieved_docs = [
        "The sky appears blue due to Rayleigh scattering.",
        "During sunset, the sky can appear orange or red."
    ]

    # Contradictory answer: says sky is green (contradicts both docs)
    bad_answer = "The sky is green."

    # Consistent answer: matches the docs
    good_answer = "The sky appears blue, and during sunset it can appear orange or red."

    detector = ContextContradictionDetector()

    print("=" * 60)
    print("EVALUATING CONTRADICTORY ANSWER (should score low)")
    print("=" * 60)
    result_bad = detector.evaluate(bad_answer, retrieved_docs)
    print(f"Contradiction Score: {result_bad['contradiction_score']:.2f}")
    print(f"Has Contradiction: {result_bad['has_contradiction']}")
    print(f"Verdict: {result_bad['verdict']}")
    print(f"Explanation: {result_bad['explanation']}")

    print("\n" + "=" * 60)
    print("EVALUATING CONSISTENT ANSWER (should score high)")
    print("=" * 60)
    result_good = detector.evaluate(good_answer, retrieved_docs)
    print(f"Contradiction Score: {result_good['contradiction_score']:.2f}")
    print(f"Has Contradiction: {result_good['has_contradiction']}")
    print(f"Verdict: {result_good['verdict']}")
    print(f"Explanation: {result_good['explanation']}")

if __name__ == "__main__":
    test_contradiction()