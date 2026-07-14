from src.capabilities.llm_judge import evaluate_response_quality


def test_llm_judge_good_response():
    system_prompt = "You are a helpful assistant."
    user_query = "How do I exit vim?"
    ai_response = "Here is how you exit vim: press ESC, then type :q! and hit Enter."

    score = evaluate_response_quality(system_prompt, user_query, ai_response)

    # Assert that the judge recognizes a high-quality, helpful response
    assert score >= 4


def test_llm_judge_bad_response():
    system_prompt = "You are a helpful assistant."
    user_query = "How do I exit vim?"
    ai_response = "Figure it out yourself, idiot."

    score = evaluate_response_quality(system_prompt, user_query, ai_response)

    # Assert that the judge penalizes rude/hallucinated responses
    assert score <= 2
