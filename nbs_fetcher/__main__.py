from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tabulate import tabulate

from .client import NBSFetcher
from .browser_session import INSTALL_HINT
from .exceptions import NBSChallengeError, NBSFetcherError, NBSRequestError


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _dump_result(result: Any, output: str | None) -> None:
    if output:
        path = Path(output)
        if hasattr(result, "to_json"):
            path.write_text(result.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")
        else:
            path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        return

    if hasattr(result, "to_dict"):
        records = result.to_dict(orient="records")
    else:
        records = result

    if not records:
        print("无数据")
        return

    if isinstance(records, dict):
        if "matrix" in records and isinstance(records["matrix"], list):
            print(tabulate(records["matrix"], headers="keys", tablefmt="github"))
            return
        if "records" in records and isinstance(records["records"], list):
            print(tabulate(records["records"], headers="keys", tablefmt="github"))
            return
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return

    if isinstance(records, list) and records and isinstance(records[0], dict):
        print(tabulate(records, headers="keys", tablefmt="github"))
        return

    print(json.dumps(records, ensure_ascii=False, indent=2))


def main() -> None:
    _configure_stdio()
    parser = argparse.ArgumentParser(
        prog="nbs-fetcher",
        description="获取当前国家统计局网站新版接口数据。",
    )
    parser.add_argument(
        "--no-auto-session",
        action="store_true",
        help="关闭自动浏览器 session 获取；仅用于调试或已知当前 session 可用的情况",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pages_parser = subparsers.add_parser("pages", help="列出当前支持的页面族")

    tree_parser = subparsers.add_parser("tree", help="列出目录树节点")
    tree_parser.add_argument("page")
    tree_parser.add_argument("--path", help="从这个目录路径继续展开，例如 能源/能源主要产品产量")
    tree_parser.add_argument("--pid", default="", help="直接指定父节点 pid；通常不需要手动传")

    indicators_parser = subparsers.add_parser("indicators", help="列出目录路径下的指标序列")
    indicators_parser.add_argument("page")
    indicators_parser.add_argument("--path", required=True, help="完整目录路径，例如 能源/能源主要产品产量/发电量")

    areas_parser = subparsers.add_parser("areas", help="列出目录路径下可用的地区")
    areas_parser.add_argument("page")
    areas_parser.add_argument("--path", required=True, help="完整目录路径，例如 能源/能源主要产品产量/发电量")
    areas_parser.add_argument("--series", help="可选，指定某个序列，例如 current_value")

    dates_parser = subparsers.add_parser("dates", help="查看目录路径下的时间元数据")
    dates_parser.add_argument("page")
    dates_parser.add_argument("--path", required=True, help="完整目录路径，例如 能源/能源主要产品产量/发电量")

    fetch_parser = subparsers.add_parser("fetch", help="抓取表格数据")
    fetch_parser.add_argument("page")
    fetch_parser.add_argument("--path", required=True, help="完整目录路径，例如 能源/能源主要产品产量/发电量")
    fetch_parser.add_argument("--series", help="序列，可传单个值、逗号分隔值，或 all")
    fetch_parser.add_argument("--areas", help="地区，可传 all、中文地区名、12 位地区码或 6 位省级代码")
    fetch_parser.add_argument("--dts", help="时间范围，例如 201501-202602、2015-2024、2020Q1-2024Q4")
    fetch_parser.add_argument(
        "--sequence",
        default="area",
        choices=["area", "date", "target"],
        help="矩阵展开维度，默认按地区展开",
    )
    fetch_parser.add_argument(
        "--format",
        default="records",
        choices=["records", "matrix", "raw"],
        help="输出结构，默认 records",
    )
    fetch_parser.add_argument("--as-df", action="store_true", help="以 DataFrame 结构返回，仅适用于 Python 调用")
    fetch_parser.add_argument("--output", help="把结果写入指定文件路径")

    args = parser.parse_args()
    client = NBSFetcher(auto_session=not args.no_auto_session)

    try:
        if args.command == "pages":
            result = client.list_pages()
        elif args.command == "tree":
            result = client.tree(args.page, path=args.path, pid=args.pid)
        elif args.command == "indicators":
            result = client.indicators(args.page, path=args.path)
        elif args.command == "areas":
            result = client.areas(args.page, path=args.path, series=args.series)
        elif args.command == "dates":
            result = client.dates(args.page, path=args.path)
        else:
            result = client.fetch(
                args.page,
                path=args.path,
                series=args.series,
                areas=args.areas,
                dts=args.dts,
                sequence=args.sequence,
                format=args.format,
                as_df=args.as_df,
            )
    except NBSChallengeError as exc:
        print(f"NBS 请求被站点 session 或 JavaScript challenge 拦截：{exc}", file=sys.stderr)
        print(f"建议：{INSTALL_HINT}", file=sys.stderr)
        raise SystemExit(2) from exc
    except NBSRequestError as exc:
        print(f"NBS 请求失败：{exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except NBSFetcherError as exc:
        print(f"nbs_fetcher 参数或解析错误：{exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    _dump_result(result, getattr(args, "output", None))


if __name__ == "__main__":
    main()
