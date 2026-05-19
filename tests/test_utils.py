from datetime import datetime
from core.utils import (
    estimate_tokens,
    clean_text,
    truncate_text,
    generate_md5,
    generate_random_string,
    extract_json_from_text,
    is_valid_date,
    is_number,
    format_file_size,
    format_tokens,
    format_tokens_with_commas,
    chunk_list,
    get_current_time,
)


class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_ascii_only(self):
        # 4 ASCII chars ≈ 1 token
        assert estimate_tokens("test") == 1

    def test_chinese_only(self):
        assert estimate_tokens("你好世界") == 4

    def test_mixed(self):
        result = estimate_tokens("hello你好")
        # 5 ASCII * 0.25 + 2 CJK * 1 = 1.25 + 2 = 3
        assert result == 3

    def test_non_string(self):
        assert estimate_tokens(123) == 0
        assert estimate_tokens(None) == 0


class TestCleanText:
    def test_strips_and_collapses_whitespace(self):
        assert clean_text("  hello   world  ") == "hello world"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_none(self):
        assert clean_text(None) == ""

    def test_newlines_and_tabs(self):
        assert clean_text("line1\n\nline2\t\tline3") == "line1 line2 line3"


class TestTruncateText:
    def test_no_truncation_needed(self):
        assert truncate_text("hello", 10) == "hello"

    def test_truncation_with_default_ellipsis(self):
        assert truncate_text("hello world", 5) == "hello..."

    def test_truncation_with_custom_ellipsis(self):
        assert truncate_text("hello world", 5, "…") == "hello…"

    def test_empty_text(self):
        assert truncate_text("", 10) == ""


class TestGenerateMd5:
    def test_known_value(self):
        assert generate_md5("hello") == "5d41402abc4b2a76b9719d911017c592"

    def test_empty_string(self):
        assert generate_md5("") == "d41d8cd98f00b204e9800998ecf8427e"


class TestGenerateRandomString:
    def test_default_length(self):
        result = generate_random_string()
        assert len(result) == 8

    def test_custom_length(self):
        result = generate_random_string(12)
        assert len(result) == 12

    def test_only_digits(self):
        result = generate_random_string(20, chars="0123456789")
        assert len(result) == 20
        assert all(c in "0123456789" for c in result)


class TestExtractJsonFromText:
    def test_plain_json_object(self):
        result = extract_json_from_text('{"a": 1}')
        assert result == {"a": 1}

    def test_plain_json_array(self):
        result = extract_json_from_text("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_markdown_code_block(self):
        text = '```json\n{"key": "value"}\n```'
        assert extract_json_from_text(text) == {"key": "value"}

    def test_markdown_without_language(self):
        text = '```\n{"x": 1}\n```'
        assert extract_json_from_text(text) == {"x": 1}

    def test_json_embedded_in_text(self):
        text = 'Some text {"hidden": [1,2]} more text'
        assert extract_json_from_text(text) == {"hidden": [1, 2]}

    def test_invalid_returns_none(self):
        assert extract_json_from_text("not json at all") is None

    def test_empty_string(self):
        assert extract_json_from_text("") is None


class TestIsValidDate:
    def test_valid_date(self):
        assert is_valid_date("2024-01-15") is True

    def test_invalid_format(self):
        assert is_valid_date("01/15/2024") is False

    def test_invalid_values(self):
        assert is_valid_date("2024-13-01") is False

    def test_non_string(self):
        assert is_valid_date(123) is False
        assert is_valid_date(None) is False

    def test_empty_string(self):
        assert is_valid_date("") is False


class TestIsNumber:
    def test_integer(self):
        assert is_number(42) is True

    def test_float(self):
        assert is_number(3.14) is True

    def test_string_number(self):
        assert is_number("42") is True
        assert is_number("3.14") is True

    def test_non_number_string(self):
        assert is_number("abc") is False

    def test_none(self):
        assert is_number(None) is False


class TestFormatFileSize:
    def test_zero(self):
        assert format_file_size(0) == "0B"

    def test_bytes(self):
        assert format_file_size(500) == "500.0 B"

    def test_kilobytes(self):
        assert format_file_size(1024) == "1.0 KB"

    def test_megabytes(self):
        assert format_file_size(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self):
        assert format_file_size(1024 ** 3) == "1.0 GB"


class TestFormatTokens:
    def test_small(self):
        assert format_tokens(500) == "500"

    def test_kilo(self):
        assert format_tokens(1500) == "1.5K"

    def test_mega(self):
        assert format_tokens(2_000_000) == "2.0M"


class TestFormatTokensWithCommas:
    def test_with_commas(self):
        assert format_tokens_with_commas(1234567) == "1,234,567"


class TestChunkList:
    def test_exact_chunks(self):
        result = list(chunk_list([1, 2, 3, 4], 2))
        assert result == [[1, 2], [3, 4]]

    def test_partial_last_chunk(self):
        result = list(chunk_list([1, 2, 3], 2))
        assert result == [[1, 2], [3]]

    def test_empty_list(self):
        result = list(chunk_list([], 3))
        assert result == []

    def test_chunk_size_larger_than_list(self):
        result = list(chunk_list([1, 2], 10))
        assert result == [[1, 2]]


class TestGetCurrentTime:
    def test_returns_iso_format_with_z(self):
        result = get_current_time()
        assert result.endswith("Z")
        # Should parse as valid ISO datetime
        dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert isinstance(dt, datetime)
