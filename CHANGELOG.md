# Changelog

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
