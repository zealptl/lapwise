"""Filter translation: wrapper hybrid syntax → OpenF1 native query parameters."""

_SUFFIX_MAP = {
    "_lt": "<",
    "_lte": "<=",
    "_gt": ">",
    "_gte": ">=",
}


def _serialize_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def translate_filters(filters: dict[str, object]) -> list[tuple[str, str]]:
    """Translate a filters dict into a list of (key, value) query-string pairs.

    Rules:
    - None values are skipped.
    - List values produce one pair per element (repeated keys).
    - Keys ending in _lt/_lte/_gt/_gte strip the suffix and emit the operator
      as part of the key name (e.g. ``lap_duration_lt`` → ``lap_duration<``).
    - Booleans are serialized as lowercase strings.
    """
    pairs: list[tuple[str, str]] = []

    for key, value in filters.items():
        if value is None:
            continue

        # Determine the effective key (strip comparison suffix if present)
        effective_key = key
        for suffix, operator in _SUFFIX_MAP.items():
            if key.endswith(suffix):
                base = key[: -len(suffix)]
                effective_key = f"{base}{operator}"
                break

        if isinstance(value, list):
            for item in value:
                pairs.append((effective_key, _serialize_value(item)))
        else:
            pairs.append((effective_key, _serialize_value(value)))

    return pairs
