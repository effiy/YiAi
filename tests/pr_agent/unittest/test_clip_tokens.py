
# Generated by CodiumAI

import pytest

from pr_agent.algo.utils import clip_tokens


class TestClipTokens:
    def test_clip(self):
        text = "line1\nline2\nline3\nline4\nline5\nline6"
        max_tokens = 25
        result = clip_tokens(text, max_tokens)
        assert result == text

        max_tokens = 10
        result = clip_tokens(text, max_tokens)
        expected_results = 'line1\nline2\nline3\n\n...(truncated)'
        assert result == expected_results
