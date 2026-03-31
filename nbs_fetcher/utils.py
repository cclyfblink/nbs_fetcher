from __future__ import annotations

import re
from typing import Iterable

from .constants import PAGE_REGISTRY, PageSpec, SERIES_TYPE_KEYWORDS, SHOW_TYPE_BY_SEQUENCE
from .exceptions import PageNotFoundError


def resolve_page(page: str) -> PageSpec:
    try:
        return PAGE_REGISTRY[page]
    except KeyError as exc:
        valid = ", ".join(sorted(spec.name for spec in {v for v in PAGE_REGISTRY.values()}))
        raise PageNotFoundError(f"Unknown page '{page}'. Valid pages: {valid}") from exc


def normalize_path(path: str | Iterable[str] | None) -> list[str]:
    if path is None:
        return []
    if isinstance(path, str):
        parts = [part.strip() for part in path.split("/")]
        return [part for part in parts if part]
    return [str(part).strip() for part in path if str(part).strip()]


def infer_series_type(label: str) -> str:
    stripped = label.strip()
    for keyword, series_type in SERIES_TYPE_KEYWORDS:
        if keyword in stripped:
            return series_type
    return stripped or "unknown"


def show_type_for_sequence(sequence: str) -> int:
    try:
        return SHOW_TYPE_BY_SEQUENCE[sequence]
    except KeyError as exc:
        valid = ", ".join(sorted(SHOW_TYPE_BY_SEQUENCE))
        raise ValueError(f"Invalid sequence '{sequence}'. Valid values: {valid}") from exc


def normalize_namespaced_label(label: str) -> str:
    return re.sub(r"\s+", " ", label).strip()


def _normalize_period_token(token: str, frequency: str) -> str:
    token = token.strip().upper()
    suffix = {"month": "MM", "quarter": "SS", "year": "YY"}[frequency]
    if token.endswith(suffix):
        return token

    digits = re.sub(r"[^0-9]", "", token)

    if frequency == "month":
        if len(digits) != 6:
            raise ValueError(f"Invalid month token '{token}'. Use YYYYMM or YYYYMMMM.")
        return f"{digits}MM"

    if frequency == "year":
        if len(digits) != 4:
            raise ValueError(f"Invalid year token '{token}'. Use YYYY or YYYYYY.")
        return f"{digits}YY"

    quarter_match = re.fullmatch(r"(\d{4})Q([1-4])", token)
    if quarter_match:
        year, quarter = quarter_match.groups()
        return f"{year}0{quarter}SS"
    if len(digits) == 6:
        return f"{digits}SS"
    raise ValueError(f"Invalid quarter token '{token}'. Use YYYYQn or YYYY0Q.")


def normalize_dts(dts: str | Iterable[str] | None, frequency: str) -> list[str] | str:
    if dts is None:
        return ""

    items = [dts] if isinstance(dts, str) else list(dts)
    normalized: list[str] = []

    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if "-" in text:
            start, end = text.split("-", 1)
            normalized.append(
                f"{_normalize_period_token(start, frequency)}-{_normalize_period_token(end, frequency)}"
            )
        else:
            normalized.append(_normalize_period_token(text, frequency))

    return normalized if normalized else ""


def coerce_list(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value if str(part).strip()]
