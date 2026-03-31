# Changelog

## [0.1.0] - 2026-03-31

### Changed
- Renamed the project from `cnstats` to `nbs_fetcher`.
- Removed the old `easyquery.htm` request path and all old `zbcode/dbcode/regcode/datestr` query semantics.
- Rebuilt the package around the current NBS API family under `/dg/website/publicrelease/web/external/...`.

### Added
- New page/path/series/areas/dts/sequence query model.
- New CLI with `pages`, `tree`, `indicators`, `areas`, `dates`, and `fetch` commands.
- New attribution note in `NOTICE` alongside the retained MIT license.
