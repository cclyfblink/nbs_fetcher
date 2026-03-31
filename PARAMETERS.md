# PARAMETERS

This document describes the current public parameter model of `nbs_fetcher`.

## Public query model

`nbs_fetcher` does not expose the retired `zbcode/dbcode/regcode/datestr` model.

It uses the current NBS website concepts instead:

- `page`
- `path`
- `series`
- `areas`
- `dts`
- `sequence`

## page

Page family name.

Currently registered pages:

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

These map internally to NBS page codes `1..10`.

## path

Catalogue path under a page.

Examples:

- `能源`
- `能源/能源主要产品产量/发电量`

`path` can be given as:

- a slash-delimited string
- a list of segments

Internally, `path` is resolved to a live `cid` and cached in memory.

## series

Indicator selection under a resolved catalogue leaf.

Accepted forms:

- `all`
- indicator id
- exact indicator label
- normalized series type such as:
  - `current_value`
  - `cumulative_value`
  - `yoy_growth`
  - `cumulative_growth`

Important note:

- In some layouts such as `sequence="area"`, the NBS API only returns one indicator per request.
- `nbs_fetcher` handles this by issuing one request per series and merging locally.

## areas

Area filter.

Accepted forms:

- `all`
- Chinese area name such as `北京市`
- 12-digit API area code such as `110000000000`
- 6-digit province code such as `110000`

`nbs_fetcher` resolves and normalizes them to the live `das` payload format.

### 6-digit area support

For area pages, the current NBS API uses 12-digit codes.

Example:

- Beijing API code: `110000000000`
- Beijing normalized 6-digit code: `110000`

`nbs_fetcher` accepts the 6-digit province code and maps it to the live 12-digit value.

## dts

Date range filter.

Accepted public forms:

- month: `201501-202602`
- year: `2015-2024`
- quarter: `2015Q1-2024Q4`

Internally these become current NBS API tokens such as:

- month: `201501MM-202602MM`
- year: `2015YY-2024YY`
- quarter: `201501SS-202404SS`

For the API request, `dts` is sent as a list.

Example:

```json
["201501MM-202602MM"]
```

If omitted, the fetcher sends an empty value and lets the site default behavior decide the window.

## sequence

Matrix focus dimension.

Accepted values:

- `area`
- `date`
- `target`

This is converted internally to the current NBS `showType` value:

- `target` -> `1`
- `date` -> `2`
- `area` -> `3`

## Internal parameters

These are not the preferred public API, but are important internally:

- `cid`
- `indicatorIds`
- `daCatalogId`
- `das`
- `showType`
- `rootId`

## Output formats

`fetch(..., format=...)` supports:

- `raw`
- `records`
- `matrix`

### raw

Returns a structured object containing:

- page metadata
- requested series
- requested areas
- requested dts
- one raw response per series request

### records

Returns a structured object containing:

- metadata
- row count
- period list
- normalized tidy `records`

If `as_df=True`, only the tidy `DataFrame` is returned.

### matrix

Returns a structured object containing:

- metadata
- period list
- `matrix`

If `as_df=True`, only the matrix `DataFrame` is returned.
