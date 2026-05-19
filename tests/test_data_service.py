import re
import pytest
from services.database.data_service import (
    _validate_collection_name,
    _build_published_date_filter,
    _handle_iso_date_filter,
    _handle_range_or_list_filter,
    _handle_string_search_filter,
    _build_filter,
    _build_sort_list,
)


class TestValidateCollectionName:
    def test_valid_name(self):
        assert _validate_collection_name("sessions") == "sessions"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="必须提供集合名称"):
            _validate_collection_name("")

    def test_none_raises(self):
        with pytest.raises(ValueError, match="必须提供集合名称"):
            _validate_collection_name(None)


class TestBuildPublishedDateFilter:
    def test_single_day(self):
        result = _build_published_date_filter("2024-01-15", "2024-01-15")
        assert "$or" in result
        patterns = [cond for cond in result["$or"]]
        # Should have patterns for pubDate, published, and isoDate
        assert len(patterns) >= 4

    def test_date_range(self):
        result = _build_published_date_filter("2024-01-01", "2024-01-02")
        assert "$or" in result

    def test_invalid_date_returns_empty(self):
        result = _build_published_date_filter("invalid", "also-invalid")
        assert result == {}


class TestHandleIsoDateFilter:
    def test_non_iso_key_returns_false(self):
        filter_dict = {}
        result = _handle_iso_date_filter("title", "test", filter_dict)
        assert result is False
        assert filter_dict == {}

    def test_range_with_comma(self):
        filter_dict = {}
        result = _handle_iso_date_filter("isoDate", "2024-01-01, 2024-01-02", filter_dict)
        assert result is True
        assert "$or" in filter_dict

    def test_single_date(self):
        filter_dict = {}
        result = _handle_iso_date_filter("isoDate", "2024-01-15", filter_dict)
        assert result is True
        assert "$or" in filter_dict

    def test_invalid_date_returns_false(self):
        filter_dict = {}
        result = _handle_iso_date_filter("isoDate", "not-a-date", filter_dict)
        assert result is False


class TestHandleRangeOrListFilter:
    def test_non_iterable_returns_false(self):
        result = _handle_range_or_list_filter("count", "not-list", {})
        assert result is False

    def test_empty_list(self):
        result = _handle_range_or_list_filter("tags", [], {})
        assert result is True

    def test_range_with_two_dates(self):
        filter_dict: dict = {}
        result = _handle_range_or_list_filter("created", ["2024-01-01", "2024-01-31"], filter_dict)
        assert result is True
        assert filter_dict == {"created": {"$gte": "2024-01-01", "$lt": "2024-01-31"}}

    def test_range_with_two_numbers(self):
        filter_dict: dict = {}
        result = _handle_range_or_list_filter("price", [10, 100], filter_dict)
        assert result is True
        assert filter_dict == {"price": {"$gte": 10.0, "$lt": 100.0}}

    def test_range_with_start_only(self):
        filter_dict: dict = {}
        result = _handle_range_or_list_filter("score", [50, "not-number"], filter_dict)
        assert result is True
        assert filter_dict == {"score": {"$gte": 50.0}}

    def test_range_with_end_only(self):
        filter_dict: dict = {}
        result = _handle_range_or_list_filter("score", ["not-number", 100], filter_dict)
        assert result is True
        assert filter_dict == {"score": {"$lt": 100.0}}

    def test_list_with_more_than_two_items(self):
        filter_dict: dict = {}
        result = _handle_range_or_list_filter("status", ["a", "b", "c"], filter_dict)
        assert result is True
        assert filter_dict == {"status": {"$in": ["a", "b", "c"]}}


class TestHandleStringSearchFilter:
    def test_non_string_returns_false(self):
        result = _handle_string_search_filter("name", 42, {})
        assert result is False

    def test_single_term(self):
        filter_dict: dict = {}
        result = _handle_string_search_filter("name", "hello", filter_dict)
        assert result is True
        assert isinstance(filter_dict["name"], re.Pattern)

    def test_multi_term_with_comma(self):
        filter_dict: dict = {}
        result = _handle_string_search_filter("name", "foo, bar", filter_dict)
        assert result is True
        assert "$or" in filter_dict
        assert len(filter_dict["$or"]) == 2

    def test_multi_term_appends_to_existing_or(self):
        filter_dict: dict = {"$or": [{"x": 1}]}
        result = _handle_string_search_filter("name", "a, b", filter_dict)
        assert result is True
        assert len(filter_dict["$or"]) == 3  # original + 2 new


class TestBuildFilter:
    def test_empty_params(self):
        assert _build_filter({}) == {}

    def test_key_field_exact_match(self):
        result = _build_filter({"key": "abc-123"})
        assert result == {"key": "abc-123"}

    def test_none_value_skipped(self):
        result = _build_filter({"name": None, "key": "x"})
        assert result == {"key": "x"}

    def test_iso_date_routing(self):
        result = _build_filter({"isoDate": "2024-01-15"})
        assert "$or" in result

    def test_numeric_value(self):
        result = _build_filter({"count": 42})
        assert result == {"count": 42}

    def test_boolean_value(self):
        result = _build_filter({"active": True})
        assert result == {"active": True}

    def test_combined_params(self):
        result = _build_filter({"key": "mykey", "name": "search", "count": 10})
        assert result["key"] == "mykey"
        assert isinstance(result["name"], re.Pattern)
        assert result["count"] == 10


class TestBuildSortList:
    def test_order_field(self):
        result = _build_sort_list("order", 1)
        assert result == [("order", 1), ("updatedTime", -1), ("createdTime", -1)]

    def test_updated_time(self):
        result = _build_sort_list("updatedTime", -1)
        # When sort is updatedTime, don't add duplicate
        assert result == [("updatedTime", -1), ("createdTime", -1)]

    def test_default_sort_param(self):
        result = _build_sort_list("title", -1)
        assert result == [
            ("title", -1),
            ("updatedTime", -1),
            ("createdTime", -1),
        ]
