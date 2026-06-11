# Changelog

## [0.1.1] - 2026-06-11

### 变更
- `fetch()` 底层数据表请求切换为当前网页端接口 `stream/esData`。
- 删除旧数据表接口 `getEsDataByCidAndDt` 的运行路径，不保留旧接口 fallback。
- `NBSFetcher` 默认启用自动 session 获取，遇到站点 session challenge 时通过 Playwright 获取网页端 cookie 并重试。
- CLI 新增 `--no-auto-session` 参数，用于调试或关闭自动 session。
- 指标序列匹配支持省略末尾单位，例如 `火力发电量` 可匹配 `火力发电量 (亿千瓦时)`。

### 新增
- 新增 Playwright 可选依赖和 Chromium 安装说明。
- 新增自动 session、`stream/esData`、常用验证命令相关文档。
- 新增测试覆盖：新数据表 endpoint、自动 cookie 注入、Playwright 缺失提示、空值保留和无单位序列匹配。

## [0.1.0] - 2026-03-31

### 变更
- 项目从 `cnstats` 改名为 `nbs_fetcher`。
- 删除旧的 `easyquery.htm` 请求路径及旧版 `zbcode/dbcode/regcode/datestr` 查询语义。
- 底层改为围绕新版国家统计局接口 `/dg/website/publicrelease/web/external/...` 重建。

### 新增
- 新的 `page/path/series/areas/dts/sequence` 参数模型。
- 新的 CLI 子命令：`pages`、`tree`、`indicators`、`areas`、`dates`、`fetch`。
- 更细化的 page registry 输出。
- `path -> cid` 内存缓存。
- `fetch()` 的 `raw / records / matrix` 规范化输出。
- `all` 地区支持和 6 位省级代码映射支持。
- 新的参数文档 `PARAMETERS.md`。
- 新的版权说明文件 `NOTICE`。
