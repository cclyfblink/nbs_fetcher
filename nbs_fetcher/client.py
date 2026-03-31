from __future__ import annotations

import copy
from typing import Any, Iterable

import pandas as pd
import requests

from .constants import (
    BASE_URL,
    DEFAULT_FS_PROVINCES,
    DEFAULT_HEADERS,
    DEFAULT_NON_AREA_VALUES,
    PRIMARY_PAGES,
)
from .exceptions import AreaNotFoundError, IndicatorNotFoundError, PathNotFoundError
from .utils import (
    coerce_list,
    infer_series_type,
    normalize_dts,
    normalize_namespaced_label,
    normalize_path,
    resolve_page,
    show_type_for_sequence,
)


class NBSFetcher:
    def __init__(self, base_url: str = BASE_URL, timeout: int = 120, verify: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify = verify
        self.session = requests.Session()
        self.session.trust_env = False
        self._root_nodes_cache: dict[str, list[dict[str, Any]]] = {}
        self._root_id_cache: dict[str, str] = {}
        self._path_cache: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        self._indicators_cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        self._areas_cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    def _headers(self, page: str) -> dict[str, str]:
        headers = dict(DEFAULT_HEADERS)
        headers["Referer"] = f"{self.base_url}/dg/website/page.html#/pc/national/{page}"
        return headers

    def _get(self, path: str, params: dict[str, Any], page: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params,
            headers=self._headers(page),
            timeout=self.timeout,
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict[str, Any], page: str) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}{path}",
            json=payload,
            headers=self._headers(page),
            timeout=self.timeout,
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()

    def list_pages(self) -> list[dict[str, Any]]:
        pages = []
        for spec in PRIMARY_PAGES:
            roots = self._root_nodes(spec.name)
            root_id = roots[0]["_id"] if roots else None
            root_name = roots[0]["name"] if roots else spec.top_label
            page_info = spec.to_dict()
            page_info["root_id"] = root_id
            page_info["root_name"] = root_name
            page_info["default_area_values"] = copy.deepcopy(DEFAULT_NON_AREA_VALUES.get(spec.name, []))
            pages.append(page_info)
        return pages

    def _root_nodes(self, page: str) -> list[dict[str, Any]]:
        if page in self._root_nodes_cache:
            return copy.deepcopy(self._root_nodes_cache[page])
        spec = resolve_page(page)
        data = self._get(
            "/dg/website/publicrelease/web/external/new/queryIndexTreeAsync",
            {"pid": "", "code": spec.code},
            spec.route,
        )
        roots = data.get("data", [])
        self._root_nodes_cache[page] = copy.deepcopy(roots)
        return copy.deepcopy(roots)

    def root_id(self, page: str) -> str:
        if page in self._root_id_cache:
            return self._root_id_cache[page]
        roots = self._root_nodes(page)
        if not roots:
            raise PathNotFoundError(f"No root node found for page '{page}'.")
        root_id = roots[0]["_id"]
        self._root_id_cache[page] = root_id
        return root_id

    def tree(self, page: str, path: str | Iterable[str] | None = None, pid: str = "") -> list[dict[str, Any]]:
        spec = resolve_page(page)
        if path is not None:
            pid = self.resolve_path(page, path)["_id"]
        data = self._get(
            "/dg/website/publicrelease/web/external/new/queryIndexTreeAsync",
            {"pid": pid, "code": spec.code},
            spec.route,
        )
        return data.get("data", [])

    def resolve_path(self, page: str, path: str | Iterable[str]) -> dict[str, Any]:
        spec = resolve_page(page)
        parts = normalize_path(path)
        cache_key = (spec.name, tuple(parts))
        if cache_key in self._path_cache:
            return copy.deepcopy(self._path_cache[cache_key])
        roots = self._root_nodes(spec.name)
        if not roots:
            raise PathNotFoundError(f"No root node found for page '{page}'.")

        current = roots[0]
        if parts and normalize_namespaced_label(parts[0]) == normalize_namespaced_label(current["name"]):
            parts = parts[1:]

        for segment in parts:
            children = self.tree(spec.name, pid=current["_id"])
            normalized_segment = normalize_namespaced_label(segment)
            match = next(
                (node for node in children if normalize_namespaced_label(node["name"]) == normalized_segment),
                None,
            )
            if match is None:
                available = ", ".join(node["name"] for node in children[:20])
                raise PathNotFoundError(
                    f"Segment '{segment}' not found under '{current['name']}'. Available children: {available}"
                )
            current = match

        self._path_cache[cache_key] = copy.deepcopy(current)
        return copy.deepcopy(current)

    def indicators(
        self,
        page: str,
        path: str | Iterable[str] | None = None,
        cid: str | None = None,
        dt: str = "",
    ) -> list[dict[str, Any]]:
        spec = resolve_page(page)
        if cid is None:
            if path is None:
                raise ValueError("Either path or cid is required.")
            cid = self.resolve_path(spec.name, path)["_id"]
        cache_key = (spec.name, cid, dt)
        if cache_key in self._indicators_cache:
            return copy.deepcopy(self._indicators_cache[cache_key])
        data = self._get(
            "/dg/website/publicrelease/web/external/new/queryIndicatorsByCid",
            {"cid": cid, "dt": dt, "name": ""},
            spec.route,
        )
        indicators = []
        for item in data.get("data", {}).get("list", []):
            indicators.append(
                {
                    "indicator_id": item.get("_id", ""),
                    "label": item.get("i_showname", "").strip(),
                    "series_type": infer_series_type(item.get("i_showname", "")),
                    "unit": item.get("du_name", item.get("du", "")),
                    "annotation": item.get("i_annotation", ""),
                    "catalog_id": item.get("catalogid", cid),
                    "raw": item,
                }
            )
        self._indicators_cache[cache_key] = copy.deepcopy(indicators)
        return copy.deepcopy(indicators)

    def dates(self, page: str, path: str | Iterable[str] | None = None, cid: str | None = None) -> dict[str, Any]:
        spec = resolve_page(page)
        if cid is None:
            if path is None:
                raise ValueError("Either path or cid is required.")
            cid = self.resolve_path(spec.name, path)["_id"]
        return self._get(
            "/dg/website/publicrelease/web/external/new/queryDtByCid",
            {"cid": cid, "rootId": self.root_id(spec.name)},
            spec.route,
        )

    def areas(
        self,
        page: str,
        path: str | Iterable[str] | None = None,
        cid: str | None = None,
        series: str | None = None,
    ) -> list[dict[str, Any]]:
        spec = resolve_page(page)
        if not spec.has_area:
            return list(DEFAULT_NON_AREA_VALUES.get(spec.name, [{"text": "全国", "value": "000000000000"}]))

        if cid is None:
            if path is None:
                raise ValueError("Either path or cid is required.")
            cid = self.resolve_path(spec.name, path)["_id"]

        cache_key = (spec.name, cid, series or "")
        if cache_key in self._areas_cache:
            return copy.deepcopy(self._areas_cache[cache_key])

        result: list[dict[str, Any]] = []
        try:
            indicator = self._pick_indicators(spec.name, cid, series)[0]
            tree_data = self._get(
                "/dg/website/publicrelease/web/external/getDaCatalogTreeByIndicatorCid",
                {"indicatorCid": indicator["indicator_id"]},
                spec.route,
            )
            nodes = tree_data.get("data", [])
            if nodes:
                da_cid = nodes[0].get("_id") or nodes[0].get("id")
                values = self._get(
                    "/dg/website/publicrelease/web/external/getDasByDaCatalogId",
                    {"daCid": da_cid},
                    spec.route,
                )
                result = [
                    {
                        "text": item.get("show_name", item.get("name_text", "")),
                        "value": item.get("name_value", ""),
                        "code6": item.get("name_value", "")[:6],
                        "raw": item,
                    }
                    for item in values.get("data", [])
                ]
        except Exception:
            result = []

        if not result and spec.name.startswith("fs"):
            result = [
                {
                    "text": item["text"],
                    "value": item["value"],
                    "code6": item["code6"],
                    "raw": item,
                }
                for item in DEFAULT_FS_PROVINCES
            ]

        self._areas_cache[cache_key] = copy.deepcopy(result)
        return result

    def _pick_indicators(self, page: str, cid: str, series: str | Iterable[str] | None) -> list[dict[str, Any]]:
        available = self.indicators(page=page, cid=cid)
        if not series or series == "all":
            return available

        requested = coerce_list(series)
        matched: list[dict[str, Any]] = []
        for wanted in requested:
            wanted_normalized = normalize_namespaced_label(wanted)
            item = next(
                (
                    indicator
                    for indicator in available
                    if wanted == indicator["indicator_id"]
                    or wanted_normalized == normalize_namespaced_label(indicator["label"])
                    or wanted == indicator["series_type"]
                ),
                None,
            )
            if item is None:
                choices = ", ".join(
                    f"{indicator['series_type']} [{indicator['indicator_id']}]"
                    for indicator in available
                )
                raise IndicatorNotFoundError(
                    f"Series '{wanted}' not found for cid '{cid}'. Available: {choices}"
                )
            matched.append(item)
        return matched

    def _resolve_area_values(
        self,
        page: str,
        cid: str,
        indicator_series: str | None,
        areas: str | Iterable[str] | None,
        sequence: str,
    ) -> list[dict[str, str]]:
        spec = resolve_page(page)
        if not spec.has_area:
            return list(DEFAULT_NON_AREA_VALUES.get(spec.name, [{"text": "全国", "value": "000000000000"}]))

        available = self.areas(spec.name, cid=cid, series=indicator_series)
        if not available:
            return []

        if areas is None:
            return available if sequence == "area" else [available[0]]

        requested = coerce_list(areas)
        if len(requested) == 1 and requested[0].lower() == "all":
            return available

        resolved = []
        for wanted in requested:
            match = next(
                (
                    area
                    for area in available
                    if wanted == area["value"]
                    or wanted == area["text"]
                    or wanted == area["code6"]
                ),
                None,
            )
            if match is None:
                raise AreaNotFoundError(f"Area '{wanted}' not found for page '{page}'.")
            resolved.append({"text": match["text"], "value": match["value"]})
        return resolved

    def _flatten_response(
        self,
        raw: dict[str, Any],
        page: str,
        cid: str,
        root_id: str,
        indicator: dict[str, Any],
    ) -> list[dict[str, Any]]:
        spec = resolve_page(page)
        records: list[dict[str, Any]] = []
        for period in raw.get("data", []):
            for item in period.get("values", []):
                area_code = item.get("areaCode", "")
                records.append(
                    {
                        "page": spec.name,
                        "page_label": spec.label,
                        "frequency": spec.frequency,
                        "cid": cid,
                        "root_id": root_id,
                        "period_code": period.get("code", ""),
                        "series_type": indicator["series_type"],
                        "indicator_id": item.get("_id", indicator["indicator_id"]),
                        "indicator_label": item.get("i_showname", indicator["label"]),
                        "unit": item.get("du_name", indicator["unit"]),
                        "area_name": item.get("area", ""),
                        "area_code": area_code,
                        "area_code6": area_code[:6],
                        "value": item.get("value", ""),
                    }
                )
        return records

    def _normalize_raw_results(
        self,
        raw_results: list[dict[str, Any]],
        page: str,
        cid: str,
        root_id: str,
        sequence: str,
        requested_areas: list[dict[str, str]],
        requested_dts: list[str] | str,
    ) -> dict[str, Any]:
        spec = resolve_page(page)
        return {
            "page": spec.name,
            "page_label": spec.label,
            "frequency": spec.frequency,
            "cid": cid,
            "root_id": root_id,
            "sequence": sequence,
            "show_type": show_type_for_sequence(sequence),
            "requested_areas": requested_areas,
            "requested_dts": requested_dts,
            "series": [item["indicator"] for item in raw_results],
            "responses": raw_results,
        }

    def _normalize_records_output(
        self,
        records: list[dict[str, Any]],
        page: str,
        cid: str,
        root_id: str,
        sequence: str,
        requested_areas: list[dict[str, str]],
        requested_dts: list[str] | str,
    ) -> dict[str, Any]:
        spec = resolve_page(page)
        period_codes = sorted({record["period_code"] for record in records}, reverse=True)
        return {
            "page": spec.name,
            "page_label": spec.label,
            "frequency": spec.frequency,
            "cid": cid,
            "root_id": root_id,
            "sequence": sequence,
            "requested_areas": requested_areas,
            "requested_dts": requested_dts,
            "row_count": len(records),
            "period_count": len(period_codes),
            "period_codes": period_codes,
            "records": records,
        }

    def _normalize_matrix_output(
        self,
        matrix: pd.DataFrame,
        page: str,
        cid: str,
        root_id: str,
        sequence: str,
        requested_areas: list[dict[str, str]],
        requested_dts: list[str] | str,
        period_order: list[str],
    ) -> dict[str, Any]:
        spec = resolve_page(page)
        return {
            "page": spec.name,
            "page_label": spec.label,
            "frequency": spec.frequency,
            "cid": cid,
            "root_id": root_id,
            "sequence": sequence,
            "requested_areas": requested_areas,
            "requested_dts": requested_dts,
            "row_count": int(len(matrix.index)),
            "period_count": len(period_order),
            "period_codes": period_order,
            "matrix": matrix,
        }

    def _to_matrix(self, records: list[dict[str, Any]], period_order: list[str]) -> pd.DataFrame:
        df = pd.DataFrame(records)
        if df.empty:
            return df
        index_fields = [
            "area_name",
            "area_code",
            "series_type",
            "indicator_id",
            "indicator_label",
            "unit",
        ]
        matrix = (
            df.pivot_table(index=index_fields, columns="period_code", values="value", aggfunc="first")
            .reset_index()
        )
        ordered_columns = [column for column in index_fields if column in matrix.columns] + [
            period for period in period_order if period in matrix.columns
        ]
        return matrix.reindex(columns=ordered_columns)

    def fetch(
        self,
        page: str,
        path: str | Iterable[str] | None = None,
        *,
        cid: str | None = None,
        series: str | Iterable[str] | None = None,
        areas: str | Iterable[str] | None = None,
        dts: str | Iterable[str] | None = None,
        sequence: str = "area",
        format: str = "records",
        as_df: bool = False,
    ) -> Any:
        spec = resolve_page(page)
        if cid is None:
            if path is None:
                raise ValueError("Either path or cid is required.")
            cid = self.resolve_path(spec.name, path)["_id"]

        indicators = self._pick_indicators(spec.name, cid, series)
        root_id = self.root_id(spec.name)
        show_type = show_type_for_sequence(sequence)
        period_filters = normalize_dts(dts, spec.frequency)
        period_order = []
        raw_results: list[dict[str, Any]] = []
        records: list[dict[str, Any]] = []
        resolved_areas_snapshot: list[dict[str, str]] | None = None

        for indicator in indicators:
            area_values = self._resolve_area_values(spec.name, cid, indicator["series_type"], areas, sequence)
            if resolved_areas_snapshot is None:
                resolved_areas_snapshot = copy.deepcopy(area_values)
            payload = {
                "cid": cid,
                "indicatorIds": [indicator["indicator_id"]],
                "daCatalogId": "",
                "das": area_values,
                "showType": show_type,
                "dts": period_filters,
                "rootId": root_id,
            }
            raw = self._post(
                "/dg/website/publicrelease/web/external/getEsDataByCidAndDt",
                payload,
                spec.route,
            )
            raw_results.append(
                {
                    "indicator": indicator,
                    "payload": payload,
                    "response": raw,
                }
            )
            if not period_order:
                period_order = [item.get("code", "") for item in raw.get("data", [])]
            records.extend(self._flatten_response(raw, spec.name, cid, root_id, indicator))

        resolved_areas_snapshot = resolved_areas_snapshot or []

        if format == "raw":
            return self._normalize_raw_results(
                raw_results,
                spec.name,
                cid,
                root_id,
                sequence,
                resolved_areas_snapshot,
                period_filters,
            )

        if format == "matrix":
            matrix = self._to_matrix(records, period_order)
            normalized = self._normalize_matrix_output(
                matrix,
                spec.name,
                cid,
                root_id,
                sequence,
                resolved_areas_snapshot,
                period_filters,
                period_order,
            )
            if as_df:
                return normalized["matrix"]
            normalized["matrix"] = normalized["matrix"].to_dict(orient="records")
            return normalized

        normalized = self._normalize_records_output(
            records,
            spec.name,
            cid,
            root_id,
            sequence,
            resolved_areas_snapshot,
            period_filters,
        )
        if as_df:
            return pd.DataFrame(normalized["records"])
        return normalized


def list_pages() -> list[dict[str, Any]]:
    return NBSFetcher().list_pages()


def tree(page: str, path: str | Iterable[str] | None = None, pid: str = "") -> list[dict[str, Any]]:
    return NBSFetcher().tree(page, path=path, pid=pid)


def indicators(page: str, path: str | Iterable[str] | None = None, cid: str | None = None) -> list[dict[str, Any]]:
    return NBSFetcher().indicators(page, path=path, cid=cid)


def areas(
    page: str,
    path: str | Iterable[str] | None = None,
    cid: str | None = None,
    series: str | None = None,
) -> list[dict[str, Any]]:
    return NBSFetcher().areas(page, path=path, cid=cid, series=series)


def dates(page: str, path: str | Iterable[str] | None = None, cid: str | None = None) -> dict[str, Any]:
    return NBSFetcher().dates(page, path=path, cid=cid)


def fetch(
    page: str,
    path: str | Iterable[str] | None = None,
    **kwargs: Any,
) -> Any:
    return NBSFetcher().fetch(page, path=path, **kwargs)
