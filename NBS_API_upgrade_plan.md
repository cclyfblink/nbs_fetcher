# cnstats NBS API Upgrade Plan

## 1. Purpose

This document records the upgrade plan for `scripts/cnstats` so it can support the current RETracker NBS update scope.

Current conclusion:

- The existing `cnstats` implementation is built on the old NBS API (`easyquery.htm`) and is no longer directly usable.
- The new NBS website is live and exposes a different API model under `/dg/website/publicrelease/web/external/...`.
- For RETracker, the highest-priority target is still feasible: provincial monthly energy generation data from NBS.

The immediate goal is not to rebuild a generic NBS client first. The goal is to restore the specific RETracker NBS update responsibilities with the smallest reliable redesign.

## 2. Existing Breakage

### 2.1 Old API endpoint is gone

Current `cnstats` uses:

- `https://data.stats.gov.cn/easyquery.htm`

Live verification result:

- Returns `404 Not Found`

Implication:

- `cnstats/common.py` request layer is broken.
- `cnstats/stats.py` assumes an old response schema with `returncode` and `returndata`, which no longer matches the live site.

### 2.2 Old query model no longer matches the site

Current model in `cnstats`:

- `zbcode`
- `dbcode`
- `regcode`
- `datestr`

New site model is centered around:

- catalog tree node ids (`cid` / catalog ids)
- indicator ids (`indicatorIds`)
- area selection via DA values (`das`)
- a root page id (`rootId`)

This means the migration is not just a URL replacement. The request contract and lookup flow changed.

## 3. New Live API Surface

The new site is hosted under:

- `https://data.stats.gov.cn/dg/website/page.html`

### 3.1 Confirmed tree-discovery endpoint

Endpoint:

- `GET /dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid=<PID>&code=<CODE>`

Purpose:

- Walk the catalog tree for each page type.

Observed `code` values:

- `1`: national monthly data
- `4`: provincial monthly data
- `6`: provincial annual data

Examples confirmed during live inspection:

- `GET /dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid=&code=4`
- `GET /dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid=f4c6cd795fea436c807163397dd36b98&code=4`
- `GET /dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid=76e04d7533764d4384b0cd8d71deccbe&code=4`
- `GET /dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid=f46bf43e25374f5b9e2181676d582356&code=4`

### 3.2 Confirmed indicator-list endpoint

Endpoint:

- `GET /dg/website/publicrelease/web/external/new/queryIndicatorsByCid?cid=<CID>&dt=<DT>&name=`

Purpose:

- Resolve a catalog node into concrete indicators.

Observed behavior:

- For a leaf-like energy topic such as provincial monthly `发电量`, this returns 4 indicators.
- These correspond to `当期值 / 累计值 / 同比增长 / 累计增长`.

Example shapes observed:

- `发电量当期值 (亿千瓦时)`
- `发电量累计值 (亿千瓦时)`
- `发电量同比增长 (%)`
- `发电量累计增长 (%)`

### 3.3 Confirmed area tree endpoint

Endpoint:

- `GET /dg/website/publicrelease/web/external/getDaCatalogTreeByIndicatorCid?indicatorCid=<INDICATOR_ID>`

Purpose:

- Discover the area catalog associated with a specific indicator.

### 3.4 Confirmed area-value endpoint

Endpoint:

- `GET /dg/website/publicrelease/web/external/getDasByDaCatalogId?daCid=<DA_CATALOG_ID>`

Purpose:

- Get selectable area values.
- Example DA values are in the style of `110000000000` for Beijing in the new site.

### 3.5 Confirmed data endpoint

Endpoint:

- `POST /dg/website/publicrelease/web/external/getEsDataByCidAndDt`

Purpose:

- Fetch the actual numeric table shown in the UI.

Confirmed live request body captured from the provincial monthly page:

```json
{
  "cid": "f76c5af9a1604d1b906463b208bdd675",
  "indicatorIds": [
    "84db18796d0147028deada513f1ef521",
    "74ad28a0ca0d4178a2b98b9340e616a0",
    "cc027e192b88404f8f7240505c791940",
    "e94ac34ce75f4c558f41c12e4f985b05"
  ],
  "daCatalogId": "",
  "das": [
    {
      "text": "北京市",
      "value": "110000000000"
    }
  ],
  "showType": "1",
  "dts": "",
  "rootId": "f4c6cd795fea436c807163397dd36b98"
}
```

Notes:

- `cid` is the catalog id for the selected topic such as provincial monthly `发电量`.
- `indicatorIds` are the metric series to include in the response.
- `das` is the selected region list.
- `rootId` appears to identify the page family, e.g. provincial monthly root.
- `dts` was empty in the captured default request. Time filtering behavior still needs explicit validation.

## 4. RETracker Scope To Support First

This plan should prioritize the current RETracker NBS responsibilities rather than generic parity with the old package.

### 4.1 Provincial monthly data required now

Confirmed live path:

- `分省月度数据 > 能源 > 能源主要产品产量 > 发电量`
- `分省月度数据 > 能源 > 能源主要产品产量 > 火力发电量`
- `分省月度数据 > 能源 > 能源主要产品产量 > 水力发电量`
- `分省月度数据 > 能源 > 能源主要产品产量 > 核能发电量`
- `分省月度数据 > 能源 > 能源主要产品产量 > 风力发电量`
- `分省月度数据 > 能源 > 能源主要产品产量 > 太阳能发电量`

Confirmed live provincial monthly leaf ids:

| Metric | Leaf name | Leaf id | Time range shown by tree |
| --- | --- | --- | --- |
| Total generation | 发电量 | `f76c5af9a1604d1b906463b208bdd675` | `1998-` |
| Thermal generation | 火力发电量 | `c81899a0508d4fdc9ad5786ef7810cca` | `1998-` |
| Hydro generation | 水力发电量 | `5a58168195604a348e6a5d909552187e` | `1998-` |
| Nuclear generation | 核能发电量 | `c8afa9ab62994303932ec9eee0b8833a` | `1998-` |
| Wind generation | 风力发电量 | `35d85b5392be4ce19cae8d6ae83932aa` | `1998-` |
| Solar generation | 太阳能发电量 | `0262c099768642d5a5dcbb5928f7c910` | `1998-` |

Confirmed live annotations:

- `主要能源产品产量月度统计范围为规模以上工业法人单位，即年主营业务收入2000万元及以上的工业企业。`

This annotation must be preserved in downstream output metadata.

### 4.2 Provincial annual data required next

Confirmed live path root:

- `分省年度数据 > 能源`

Confirmed live annual energy catalog children under `分省年度数据 > 能源`:

- `主要能源产品产量` with id `ade19f093ebe43a5a773087039c5fedc`
- `主要能源产品消费量` with id `ccc1ef64e4a0485f840cd5f6fa192097`

Observed annual annotations:

- `主要能源产品消费量` includes note: `此表中电力消费量为中电联数据。`

Important note:

- The exact annual leaf ids for `发电量` and `电力消费量` under these annual catalogs were not fully enumerated in this pass.
- They should be treated as the first follow-up validation task during implementation.

### 4.3 Metrics to prioritize for RETracker implementation

Priority 1:

- Provincial monthly `发电量`
- Provincial monthly `风力发电量`
- Provincial monthly `太阳能发电量`

Priority 2:

- Provincial annual `发电量`
- Provincial annual `电力消费量`

Priority 3:

- Provincial monthly `火力 / 水力 / 核能发电量`
- Additional annual calibration tables if needed for later methodology work

## 5. Expected Value Types

For provincial monthly energy generation topics, the new site returns 4 indicator series per topic:

1. `当期值`
2. `累计值`
3. `同比增长 (%)`
4. `累计增长 (%)`

For RETracker, the immediate target values should be:

- `当期值` as the primary fact table input
- `累计值` as an optional validation helper
- growth rates only if explicitly needed for QA or source notes

Recommended default extraction policy:

- Store all four series in raw extraction output
- Promote only `当期值` into the primary structured monthly generation table unless another series is explicitly needed

## 6. Time Range Notes

### 6.1 What the new tree claims

Provincial monthly energy generation leaf nodes show:

- `sdate = 1998`
- `edate = null`

Provincial annual energy catalog `主要能源产品产量` shows:

- `sdate = 1991`

### 6.2 What still needs verification

The tree metadata only tells us the declared coverage. It does not yet prove:

- whether every region has complete monthly history back to `1998`
- how the site handles January/February merged publication windows
- whether all historical periods are accessible in one request or require explicit time slicing

Implementation must validate:

- default response window if `dts` is empty
- accepted `dts` format
- whether large historical requests need chunking

## 7. Area / Region Coding Notes

Old `cnstats` used old-style region codes such as:

- `110000` for Beijing

The new site request body uses DA values such as:

- `110000000000` for Beijing

Implication:

- We should preserve public-facing province codes as canonical RETracker identifiers, e.g. `110000`
- But the new client will need a lookup table between old six-digit province codes and new DA values

Suggested rule:

- External API layer uses new DA values
- Structured output normalizes back to six-digit provincial codes

## 8. Code Impact Range

The following files are directly affected.

### 8.1 Must change

- `scripts/cnstats/cnstats/common.py`
  - replace old `easyquery.htm` client
  - add new request helpers for tree discovery, indicator discovery, area discovery, and data fetch

- `scripts/cnstats/cnstats/stats.py`
  - current old-schema parser is no longer valid
  - redesign around new catalog/indicator/data pipeline

- `scripts/cnstats/cnstats/regcode.py`
  - old region discovery depends on old API
  - should move to DA catalog / DA values lookup for the new site

- `scripts/cnstats/cnstats/zbcode.py`
  - old `zbcode` tree traversal depends on old API and old indicator-code taxonomy
  - likely needs a compatibility wrapper or a replacement abstraction

- `scripts/cnstats/cnstats/__main__.py`
  - CLI semantics currently assume `zbcode + dbcode + regcode + date`
  - CLI will need either a compatibility layer or a new command mode aligned with the new site

### 8.2 Must add or heavily redesign

Recommended new modules:

- `scripts/cnstats/cnstats/catalog.py`
  - tree walking by page code and parent id

- `scripts/cnstats/cnstats/indicators.py`
  - list indicators for a catalog leaf

- `scripts/cnstats/cnstats/areas.py`
  - resolve DA catalogs and region values

- `scripts/cnstats/cnstats/client.py`
  - thin HTTP client for new API surface

- `scripts/cnstats/cnstats/mappings.py`
  - RETracker-oriented static mappings for target leaf ids and province code normalization

### 8.3 Tests that must be replaced or extended

Current tests such as `tests/test_api_vcr.py` are built around old `zbcode` requests and old VCR payloads.

They should be replaced or supplemented with tests that cover:

- tree discovery by page code
- provincial monthly generation leaf lookup
- indicator resolution for `当期值 / 累计值 / 同比 / 累计增长`
- area mapping for all provinces
- live response parsing into a tidy table

## 9. Recommended Upgrade Strategy

### Phase 1: Restore only RETracker-critical provincial monthly extraction

Implement:

- page code `4` tree discovery
- hardcoded mapping for provincial monthly generation leaf ids listed in this document
- one function to fetch all provinces for one leaf topic
- output normalized rows with:
  - `source = NBS`
  - `dataset = provincial_monthly_energy`
  - `metric_name`
  - `metric_series_type`
  - `province_code`
  - `province_name`
  - `date`
  - `value`
  - `unit`
  - `coverage_note`

This phase should target:

- `发电量`
- `风力发电量`
- `太阳能发电量`

### Phase 2: Add annual calibration support

Implement:

- page code `6` tree discovery
- annual energy catalog traversal
- annual `发电量` extraction
- annual `电力消费量` extraction

### Phase 3: Decide compatibility policy for old `zbcode` interface

Two possible paths:

1. Compatibility-first
   - keep `stats(zbcode, datestr, regcode, dbcode)` public API
   - maintain an internal mapping from old code concepts to new catalog ids where possible

2. New-model-first
   - introduce new high-level methods for the new site
   - leave old API as deprecated or limited compatibility mode

Recommended choice for RETracker use:

- Prefer new-model-first internally.
- Only add compatibility wrappers where it saves migration effort.

## 10. Concrete Targets For RETracker

The following specific values should be reachable after the first successful upgrade.

### 10.1 Provincial monthly generation targets

- Beijing monthly total generation
- Beijing monthly wind generation
- Beijing monthly solar generation
- All 31 provincial-level regions for the same three metrics

Expected table concepts:

- total monthly generation by province
- wind monthly generation by province
- solar monthly generation by province

### 10.2 Value-series coverage to keep

For each metric, keep these raw series:

- `当期值`
- `累计值`
- `同比增长 (%)`
- `累计增长 (%)`

### 10.3 Region scope

Expected provincial coverage:

- 31 provincial-level regions in the NBS provincial pages

Do not assume:

- Hong Kong
- Macao
- Taiwan

unless they are explicitly requested through separate page families.

## 11. Open Validation Items

These items still need explicit implementation-time validation.

1. Exact response schema of `getEsDataByCidAndDt`
   - column names
   - time keys
   - area row structure

2. Accepted `dts` format
   - empty vs explicit year range vs explicit month range

3. Best bulk-fetch strategy
   - one province per request
   - multi-province request in one payload
   - one leaf at a time vs combined topics

4. Annual leaf ids under:
   - `分省年度数据 > 能源 > 主要能源产品产量`
   - `分省年度数据 > 能源 > 主要能源产品消费量`

5. Whether historical responses are paginated or truncated in large windows

6. Whether solar unit in the new site is now aligned with `亿千瓦时` or still diverges in some annual tables

## 12. Suggested Immediate Implementation Order

1. Add a new low-level client for the `/dg/website/publicrelease/web/external/...` API family.
2. Add catalog discovery for code `4` and resolve the confirmed provincial monthly generation leaf ids.
3. Parse one full provincial monthly `发电量` response into tidy rows.
4. Add province normalization and metadata retention.
5. Add `风力发电量` and `太阳能发电量` using the same pipeline.
6. Only after that, extend into annual energy extraction under code `6`.

## 13. Practical Recommendation

For RETracker, treat the old `cnstats` package as:

- reusable project skeleton
- not reusable request logic

The fastest reliable path is:

- keep package layout
- replace transport and discovery logic
- target RETracker's NBS scope first
- postpone generic backward compatibility until after the provincial monthly pipeline works
