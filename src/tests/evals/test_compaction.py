from src.capabilities.compaction import compact_context


def test_compaction():
    messages = [{"role": "assistant", "content": "Sure! Here is the code."} for _ in range(25)]
    compacted = compact_context(messages)

    # Assert limit = 10 messages
    assert len(compacted) == 10

    # Assert system prompt at index 0
    assert compacted[0]["role"] == "system"
    assert compacted[0]["content"] == "You are a helpful AI."

    # Assert boilerplate removed
    for msg in compacted[1:]:
        assert "Sure! " not in msg["content"]
        assert msg["content"] == "Here is the code."
