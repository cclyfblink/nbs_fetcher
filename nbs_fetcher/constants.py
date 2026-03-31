from __future__ import annotations

from dataclasses import asdict, dataclass


BASE_URL = "https://data.stats.gov.cn"


@dataclass(frozen=True)
class PageSpec:
    name: str
    code: int
    label: str
    frequency: str
    has_area: bool
    route: str
    aliases: tuple[str, ...] = ()
    top_label: str | None = None
    supports_tree: bool = True
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PRIMARY_PAGES = (
    PageSpec("monthData", 1, "月度数据", "month", False, "monthData", top_label="月度数据"),
    PageSpec("quarterData", 2, "季度数据", "quarter", False, "quarterData", top_label="季度数据"),
    PageSpec("yearData", 3, "年度数据", "year", False, "yearData", top_label="年度数据"),
    PageSpec("fsMonthData", 4, "分省月度数据", "month", True, "fsMonthData", top_label="分省月度数据"),
    PageSpec("fsQuarterData", 5, "分省季度数据", "quarter", True, "fsQuarterData", top_label="分省季度数据"),
    PageSpec("fsYearData", 6, "分省年度数据", "year", True, "fsYearData", top_label="分省年度数据"),
    PageSpec(
        "mainMonthData",
        7,
        "主要城市月度价格",
        "month",
        True,
        "mainMonthData",
        aliases=("gjscMonthPrice",),
        top_label="主要城市月度价格",
    ),
    PageSpec("mainYearData", 8, "主要城市年度数据", "year", True, "mainYearData", top_label="主要城市年度数据"),
    PageSpec("gatMonthData", 9, "港澳台月度数据", "month", True, "gatMonthData", top_label="港澳台月度数据"),
    PageSpec("gatYearData", 10, "港澳台年度数据", "year", True, "gatYearData", top_label="港澳台年度数据"),
)


PAGE_REGISTRY: dict[str, PageSpec] = {}
for spec in PRIMARY_PAGES:
    PAGE_REGISTRY[spec.name] = spec
    for alias in spec.aliases:
        PAGE_REGISTRY[alias] = spec


PRIMARY_PAGE_NAMES = tuple(spec.name for spec in PRIMARY_PAGES)


SHOW_TYPE_BY_SEQUENCE = {
    "target": 1,
    "date": 2,
    "area": 3,
}


DEFAULT_HEADERS = {
    "Origin": BASE_URL,
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
}


SERIES_TYPE_KEYWORDS = (
    ("累计增长", "cumulative_growth"),
    ("同比增长", "yoy_growth"),
    ("累计值", "cumulative_value"),
    ("当期值", "current_value"),
)


DEFAULT_NON_AREA_VALUES = {
    "monthData": [{"text": "全国", "value": "000000000000"}],
    "quarterData": [{"text": "全国", "value": "000000000000"}],
    "yearData": [{"text": "全国", "value": "000000000000"}],
}


DEFAULT_FS_PROVINCES = [
    {"text": "北京市", "value": "110000000000", "code6": "110000"},
    {"text": "天津市", "value": "120000000000", "code6": "120000"},
    {"text": "河北省", "value": "130000000000", "code6": "130000"},
    {"text": "山西省", "value": "140000000000", "code6": "140000"},
    {"text": "内蒙古自治区", "value": "150000000000", "code6": "150000"},
    {"text": "辽宁省", "value": "210000000000", "code6": "210000"},
    {"text": "吉林省", "value": "220000000000", "code6": "220000"},
    {"text": "黑龙江省", "value": "230000000000", "code6": "230000"},
    {"text": "上海市", "value": "310000000000", "code6": "310000"},
    {"text": "江苏省", "value": "320000000000", "code6": "320000"},
    {"text": "浙江省", "value": "330000000000", "code6": "330000"},
    {"text": "安徽省", "value": "340000000000", "code6": "340000"},
    {"text": "福建省", "value": "350000000000", "code6": "350000"},
    {"text": "江西省", "value": "360000000000", "code6": "360000"},
    {"text": "山东省", "value": "370000000000", "code6": "370000"},
    {"text": "河南省", "value": "410000000000", "code6": "410000"},
    {"text": "湖北省", "value": "420000000000", "code6": "420000"},
    {"text": "湖南省", "value": "430000000000", "code6": "430000"},
    {"text": "广东省", "value": "440000000000", "code6": "440000"},
    {"text": "广西壮族自治区", "value": "450000000000", "code6": "450000"},
    {"text": "海南省", "value": "460000000000", "code6": "460000"},
    {"text": "重庆市", "value": "500000000000", "code6": "500000"},
    {"text": "四川省", "value": "510000000000", "code6": "510000"},
    {"text": "贵州省", "value": "520000000000", "code6": "520000"},
    {"text": "云南省", "value": "530000000000", "code6": "530000"},
    {"text": "西藏自治区", "value": "540000000000", "code6": "540000"},
    {"text": "陕西省", "value": "610000000000", "code6": "610000"},
    {"text": "甘肃省", "value": "620000000000", "code6": "620000"},
    {"text": "青海省", "value": "630000000000", "code6": "630000"},
    {"text": "宁夏回族自治区", "value": "640000000000", "code6": "640000"},
    {"text": "新疆维吾尔自治区", "value": "650000000000", "code6": "650000"},
]
