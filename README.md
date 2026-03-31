# nbs_fetcher

`nbs_fetcher` is a Python package for the current National Bureau of Statistics website API at:

- `https://data.stats.gov.cn/dg/website/publicrelease/web/external/...`

This project is derived from the MIT-licensed `cnstats` project by sj, but it no longer uses the retired `easyquery.htm` interface or the old `zbcode/dbcode/regcode/datestr` parameter model.

## License and attribution

- Original upstream project: `songjian/cnstats`
- Original license: MIT
- This repository retains the original MIT license in `LICENSE`
- Additional attribution notes are recorded in `NOTICE`

## What changed

The old NBS path used by `cnstats`:

- `https://data.stats.gov.cn/easyquery.htm`

now returns `404 Not Found`.

`nbs_fetcher` is built around the current API family:

- `queryIndexTreeAsync`
- `queryIndicatorsByCid`
- `queryDtByCid`
- `getDaCatalogTreeByIndicatorCid`
- `getDasByDaCatalogId`
- `getEsDataByCidAndDt`

## Installation

```bash
pip install -e .
```

or with uv:

```bash
uv sync
```

## Core model

The public API is organized around the current NBS website concepts:

- `page`: page family such as `fsMonthData`
- `path`: catalogue path such as `能源/能源主要产品产量/发电量`
- `series`: indicator series such as `current_value`
- `areas`: area filter such as `all` or `北京市`
- `dts`: date range such as `201501-202602`
- `sequence`: matrix dimension focus such as `area`, `date`, or `target`

## Python examples

List supported pages:

```python
from nbs_fetcher import list_pages

print(list_pages())
```

Each page entry now includes extra metadata such as:

- `code`
- `frequency`
- `has_area`
- `root_id`
- `root_name`
- `aliases`

Browse a tree branch:

```python
from nbs_fetcher import tree

nodes = tree("fsMonthData", path="能源")
for node in nodes:
    print(node["name"], node["_id"])
```

List indicators:

```python
from nbs_fetcher import indicators

items = indicators("fsMonthData", path="能源/能源主要产品产量/发电量")
for item in items:
    print(item["series_type"], item["indicator_id"], item["label"])
```

Fetch provincial monthly generation as a tidy DataFrame:

```python
from nbs_fetcher import fetch

df = fetch(
    "fsMonthData",
    path="能源/能源主要产品产量/发电量",
    series=["current_value", "cumulative_value"],
    areas="all",
    dts="201501-202602",
    sequence="area",
    as_df=True,
)

print(df.head())
```

By default, `format="records"` returns a structured object with metadata and a `records` list.
If `as_df=True`, only the tidy DataFrame is returned.

Fetch a matrix layout:

```python
from nbs_fetcher import fetch

matrix = fetch(
    "fsMonthData",
    path="能源/能源主要产品产量/发电量",
    series=["current_value", "cumulative_value"],
    areas="all",
    dts="201501-202602",
    sequence="area",
    format="matrix",
    as_df=True,
)

print(matrix.head())
```

With `format="matrix"` and `as_df=False`, the fetcher returns a structured object with metadata and a `matrix` list.

Area filters support:

- `all`
- Chinese names such as `北京市`
- live 12-digit area codes such as `110000000000`
- normalized 6-digit province codes such as `110000`

`path -> cid` resolution is cached in memory inside the client instance.

## CLI examples

List page families:

```bash
python -m nbs_fetcher pages
```

Browse a tree:

```bash
python -m nbs_fetcher tree fsMonthData --path "能源"
```

List indicators:

```bash
python -m nbs_fetcher indicators fsMonthData --path "能源/能源主要产品产量/发电量"
```

List areas:

```bash
python -m nbs_fetcher areas fsMonthData --path "能源/能源主要产品产量/发电量" --series current_value
```

Fetch data:

```bash
python -m nbs_fetcher fetch fsMonthData --path "能源/能源主要产品产量/发电量" --series current_value,cumulative_value --areas all --dts 201501-202602 --sequence area --format matrix
```

## Supported pages in the current registry

- `monthData`
- `quarterData`
- `yearData`
- `fsMonthData`
- `fsQuarterData`
- `fsYearData`
- `mainMonthData`
- `mainYearData`
- `gatMonthData`
- `gatYearData`

## Notes

- The current NBS API uses opaque ids such as `cid`, `indicatorId`, and `rootId`
- Province values are 12-digit area codes in the live API
- The fetcher accepts 6-digit province codes and maps them to the live 12-digit values
- In some layouts, multi-series requests need to be split into one request per series and merged locally
- This package intentionally does not preserve the old `easyquery.htm` compatibility layer
- Parameter details are documented in `PARAMETERS.md`
