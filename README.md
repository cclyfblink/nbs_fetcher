# nbs_fetcher

`nbs_fetcher` 是面向国家统计局新版数据站点 `data.stats.gov.cn` 的 Python 抓取工具，当前适配以下接口族：

- `queryIndexTreeAsync`
- `queryIndicatorsByCid`
- `queryDtByCid`
- `getDaCatalogTreeByIndicatorCid`
- `getDasByDaCatalogId`
- `getEsDataByCidAndDt`

本目录是一个独立的 Python 包，已包含：

- Python API
- CLI 入口
- 参数文档 `PARAMETERS.md`
- 基础测试目录 `tests/`

> [!NOTE]
> 看不懂？把这个仓库发给AI，让它帮你做吧。

## 项目边界

本项目基于 MIT 协议项目 `songjian/cnstats` 改造，但目标已经切换到新版国家统计局站点。

当前实现不再兼容旧版 `easyquery.htm` 查询模型，也不保留旧参数体系：

- `zbcode`
- `dbcode`
- `regcode`
- `datestr`

对外公开的参数模型已重构为：

- `page`
- `path`
- `series`
- `areas`
- `dts`
- `sequence`

## 法律与合规提示

本工具用于访问国家统计局公开站点的现行接口，但“技术上可访问”不等于“任何使用方式都当然合规”。在实际使用前，请自行评估并承担相应的法律、合规与内部治理责任，至少应关注以下事项：

- 是否符合国家统计局网站的服务条款、robots 约束、访问频率要求及其他公开规则
- 是否存在对站点造成异常压力的批量抓取、并发请求、长期轮询或镜像式采集行为
- 是否涉及将抓取结果用于商业分发、再销售、付费产品、对外 API、模型训练或其他二次利用场景
- 是否需要在内部项目、客户交付或公开发布中保留原始来源、发布日期、口径说明和版权声明
- 是否存在数据更新后继续沿用旧口径、旧基期或旧目录结构而造成误导性使用的风险

使用建议：

- 控制请求频率，避免高并发和无必要的重复抓取
- 优先抓取研究或交付所必需的最小数据范围
- 在下游文件、数据库或报告中保留来源标识与时间戳
- 如拟用于商业化、公开分发或大规模自动化采集，建议先由使用方自行完成法务与合规审查

本项目不提供法律意见，也不对使用者的具体用途、抓取规模、再分发方式或由此产生的合规后果承担保证责任

## 安装

在当前目录下执行：

```bash
pip install -e .
```

或：

```bash
uv sync
```

## 使用流程

新版站点的查询逻辑可以概括为四步：

1. 确定数据所属 `page`
2. 通过目录树确认 `path`
3. 查看该路径下可用的 `series`
4. 调用 `fetch()` 抓取数据

推荐按这个顺序使用以下接口：

1. `list_pages()`
2. `tree()`
3. `indicators()`
4. `fetch()`

## 快速示例

以下示例查询 `fsMonthData` 中 `能源/能源主要产品产量/发电量` 的当期值与累计值。

### 1. 查看 page

```python
from nbs_fetcher import list_pages

for item in list_pages():
    print(item["name"], item["label"], item["frequency"])
```

如需查询分省月度数据，应使用：

- `fsMonthData`

### 2. 查看目录树

```python
from nbs_fetcher import tree

nodes = tree("fsMonthData", path="能源")
for node in nodes:
    print(node["name"], node["_id"])
```

继续向下展开：

```python
nodes = tree("fsMonthData", path="能源/能源主要产品产量")
for node in nodes:
    print(node["name"], node["_id"])
```

确认完整路径：

- `能源/能源主要产品产量/发电量`

### 3. 查看指标序列

```python
from nbs_fetcher import indicators

items = indicators("fsMonthData", path="能源/能源主要产品产量/发电量")
for item in items:
    print(item["series_type"], item["label"], item["unit"])
```

常见输出包括：

- `current_value`
- `cumulative_value`
- `yoy_growth`
- `cumulative_growth`

### 4. 抓取数据

```python
from nbs_fetcher import fetch

result = fetch(
    "fsMonthData",
    path="能源/能源主要产品产量/发电量",
    series=["current_value", "cumulative_value"],
    areas="all",
    dts="201501-202602",
    sequence="area",
    format="records",
)

print(result["row_count"])
print(result["records"][:2])
```

单省查询示例：

```python
result = fetch(
    "fsMonthData",
    path="能源/能源主要产品产量/发电量",
    series="current_value",
    areas="110000",
    dts="202401-202412",
    format="records",
)
```

其中：

- `110000` 表示北京市
- `areas` 也可写为 `北京市` 或 `110000000000`

## Python API

### `list_pages()`

列出当前内置页面注册表及页面元数据。

```python
from nbs_fetcher import list_pages

pages = list_pages()
print(pages)
```

每个页面项通常包含：

- `name`
- `code`
- `label`
- `frequency`
- `has_area`
- `route`
- `aliases`
- `root_id`
- `root_name`

### `tree(page, path=None, pid="")`

按目录树逐层浏览节点。适用于尚未确定完整 `path` 的场景。

```python
from nbs_fetcher import tree

tree("fsMonthData", path="能源")
```

### `indicators(page, path=None, cid=None)`

列出某个目录节点下的指标序列。

```python
from nbs_fetcher import indicators

items = indicators("fsMonthData", path="能源/能源主要产品产量/发电量")
```

### `areas(page, path=None, cid=None, series=None)`

列出某个目录节点和序列下可用的地区值。

```python
from nbs_fetcher import areas

items = areas(
    "fsMonthData",
    path="能源/能源主要产品产量/发电量",
    series="current_value",
)
```

### `dates(page, path=None, cid=None)`

查看当前目录的时间元数据。

```python
from nbs_fetcher import dates

items = dates("fsMonthData", path="能源/能源主要产品产量/发电量")
```

### `fetch(page, path=None, ...)`

抓取数据主入口。

```python
from nbs_fetcher import fetch

result = fetch(
    "fsMonthData",
    path="能源/能源主要产品产量/发电量",
    series=["current_value", "cumulative_value"],
    areas="all",
    dts="201501-202602",
    sequence="area",
    format="records",
)
```

当 `as_df=True` 时，`records` 和 `matrix` 会直接返回 `pandas.DataFrame`。

## CLI

### 页面列表

```bash
python -m nbs_fetcher pages
```

### 目录树

```bash
python -m nbs_fetcher tree fsMonthData --path "能源"
```

### 指标序列

```bash
python -m nbs_fetcher indicators fsMonthData --path "能源/能源主要产品产量/发电量"
```

### 地区列表

```bash
python -m nbs_fetcher areas fsMonthData --path "能源/能源主要产品产量/发电量" --series current_value
```

### 抓取数据

```bash
python -m nbs_fetcher fetch fsMonthData --path "能源/能源主要产品产量/发电量" --series current_value,cumulative_value --areas all --dts 201501-202602 --sequence area --format matrix
```

### 写入文件

```bash
python -m nbs_fetcher fetch fsMonthData --path "能源/能源主要产品产量/发电量" --series current_value --areas 110000 --dts 202401-202412 --format records --output output.json
```

`--output` 当前的导出行为如下：

- 正式支持的导出内容类型：`JSON` 文本
- 推荐文件扩展名：`.json`
- 文件编码：`UTF-8`

当前实现说明：

- 当输出对象是结构化结果时，写入的是 JSON 对象
- 当输出对象是 `DataFrame` 时，写入的是 `orient="records"` 的 JSON 数组
- CLI 不会根据文件扩展名自动转换为 `csv`、`xlsx`、`parquet`

因此，下面这些写法在当前版本中**不建议**使用为正式导出格式：

- `output.csv`
- `output.xlsx`
- `output.parquet`

即使传入这些扩展名，当前写入内容仍然是 JSON 文本，而不是对应格式的二进制文件。

## 页面注册表

当前内置页面如下：

| page | 中文名称 | 频率 | 地区维度 | 说明 |
|------|----------|------|----------|------|
| `monthData` | 月度数据 | month | 否 | 全国月度 |
| `quarterData` | 季度数据 | quarter | 否 | 全国季度 |
| `yearData` | 年度数据 | year | 否 | 全国年度 |
| `fsMonthData` | 分省月度数据 | month | 是 | 省级月度 |
| `fsQuarterData` | 分省季度数据 | quarter | 是 | 省级季度 |
| `fsYearData` | 分省年度数据 | year | 是 | 省级年度 |
| `mainMonthData` | 主要城市月度价格 | month | 是 | 主要城市月度价格 |
| `mainYearData` | 主要城市年度数据 | year | 是 | 主要城市年度 |
| `gatMonthData` | 港澳台月度数据 | month | 是 | 港澳台月度 |
| `gatYearData` | 港澳台年度数据 | year | 是 | 港澳台年度 |

参数可输入值、地区代码、时间格式、输出结构等完整说明见：`PARAMETERS.md`

## 实现说明

- `path -> cid` 解析结果会在 client 实例内缓存
- 顶层函数默认复用同一个内部 client，因此单次运行可共享缓存
- 对分省页面，外部可直接传 6 位省级代码，内部会映射为新版接口使用的 12 位地区值
- 某些布局下多个序列会拆成多次请求，再在本地合并结果

## 已知边界

- 当前默认 `verify=False`，请求时会出现 HTTPS 证书校验告警
- `mainMonthData`、`mainYearData`、`gatMonthData`、`gatYearData` 的地区集合依赖实时接口返回，不在代码中固化
- `areas()` 对城市页和港澳台页优先走实时接口；只有分省页内置了固定省级映射表
- 本项目不提供旧版 `cnstats` 接口兼容层

## 版权与署名

- Upstream: `songjian/cnstats`
- License: MIT
- 本仓库保留原始 `LICENSE`
- 额外说明见 `NOTICE`
