"""Unit tests for lapwise.clients.filters.translate_filters."""

from lapwise.clients.filters import translate_filters


def test_equality_str_passes_through() -> None:
    result = translate_filters({"driver_number": 4})
    assert ("driver_number", "4") in result


def test_equality_float_passes_through() -> None:
    result = translate_filters({"speed": 3.14})
    assert ("speed", "3.14") in result


def test_none_values_skipped() -> None:
    result = translate_filters({"driver_number": None, "session_key": 9165})
    keys = [k for k, _ in result]
    assert "driver_number" not in keys
    assert "session_key" in keys


def test_list_values_become_repeated_keys() -> None:
    result = translate_filters({"driver_number": [4, 81]})
    assert result == [("driver_number", "4"), ("driver_number", "81")]


def test_lt_suffix_translates() -> None:
    result = translate_filters({"stop_duration_lt": 2.3})
    assert ("stop_duration<", "2.3") in result


def test_lte_suffix_translates() -> None:
    result = translate_filters({"position_lte": 3})
    assert ("position<=", "3") in result


def test_gt_suffix_translates() -> None:
    result = translate_filters({"lap_number_gt": 10})
    assert ("lap_number>", "10") in result


def test_gte_suffix_translates() -> None:
    result = translate_filters({"wind_direction_gte": 130})
    assert ("wind_direction>=", "130") in result


def test_bool_false_serialized_lowercase() -> None:
    result = translate_filters({"is_pit_out_lap": False})
    assert ("is_pit_out_lap", "false") in result


def test_bool_true_serialized_lowercase() -> None:
    result = translate_filters({"is_pit_out_lap": True})
    assert ("is_pit_out_lap", "true") in result


def test_empty_filters_returns_empty() -> None:
    assert translate_filters({}) == []


def test_all_none_returns_empty() -> None:
    assert translate_filters({"a": None, "b": None}) == []


def test_mixed_filters() -> None:
    result = translate_filters(
        {
            "session_key": 9165,
            "driver_number": [1, 44],
            "lap_duration_lt": 90.0,
            "dnf": None,
        }
    )
    assert ("session_key", "9165") in result
    assert ("driver_number", "1") in result
    assert ("driver_number", "44") in result
    assert ("lap_duration<", "90.0") in result
    dnf_keys = [k for k, _ in result if k == "dnf"]
    assert dnf_keys == []
