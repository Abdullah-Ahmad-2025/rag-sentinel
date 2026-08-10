import pytest
from backend.evaluators.citation import CitationAccuracyEvaluator


@pytest.fixture
def evaluator():
    return CitationAccuracyEvaluator()


DOCS = [
    "Paris is the capital of France. It is located on the Seine River.",
    "The Eiffel Tower is a famous landmark in Paris.",
    "France is a country in Western Europe with a population of 67 million.",
]


def test_valid_citations(evaluator):
    answer = (
        "Paris is the capital of France [1]. "
        "The Eiffel Tower is a famous landmark in Paris [2]."
    )
    result = evaluator.evaluate(answer, DOCS)
    assert result["citation_accuracy"] == 1.0
    assert result["valid_citations"] == 2
    assert result["total_citations"] == 2


def test_invalid_index_citations(evaluator):
    answer = (
        "Paris is the capital of France [5]. "
        "France has a population of 67 million [10]."
    )
    result = evaluator.evaluate(answer, DOCS)
    assert result["citation_accuracy"] == 0.0
    assert result["valid_citations"] == 0
    assert len(result["invalid_citations"]) == 2


def test_comma_separated_citations(evaluator):
    answer = "Paris is the capital of France [1,2]."
    result = evaluator.evaluate(answer, DOCS)
    assert result["total_citations"] == 1
    assert result["citation_accuracy"] == 1.0


def test_source_format_citations(evaluator):
    answer = "Paris is the capital of France [source1]."
    result = evaluator.evaluate(answer, DOCS)
    assert result["total_citations"] == 1
    assert result["citation_accuracy"] == 1.0


def test_quoted_text_verification(evaluator):
    answer = '"Paris is the capital of France" [1].'
    result = evaluator.evaluate(answer, DOCS)
    assert result["citation_accuracy"] == 1.0


def test_hallucinated_content_with_valid_index(evaluator):
    answer = "The moon is made of cheese [1]."
    result = evaluator.evaluate(answer, DOCS)
    assert result["citation_accuracy"] == 0.0
    assert result["valid_citations"] == 0


def test_no_citations_returns_perfect_score(evaluator):
    answer = "Paris is a beautiful city."
    result = evaluator.evaluate(answer, DOCS)
    assert result["citation_accuracy"] == 1.0
    assert result["total_citations"] == 0


def test_one_indexed_first_document(evaluator):
    answer = "Paris is the capital of France [1]."
    result = evaluator.evaluate(answer, DOCS)
    assert result["citation_accuracy"] == 1.0
