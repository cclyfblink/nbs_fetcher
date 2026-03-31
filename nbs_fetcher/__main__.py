from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tabulate import tabulate

from .client import NBSFetcher


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
        print("No data")
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
    parser = argparse.ArgumentParser(
        prog="nbs-fetcher",
        description="Fetch data from the current National Bureau of Statistics website API.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pages_parser = subparsers.add_parser("pages", help="List supported page families")

    tree_parser = subparsers.add_parser("tree", help="List catalogue tree nodes")
    tree_parser.add_argument("page")
    tree_parser.add_argument("--path")
    tree_parser.add_argument("--pid", default="")

    indicators_parser = subparsers.add_parser("indicators", help="List indicators under a catalogue path")
    indicators_parser.add_argument("page")
    indicators_parser.add_argument("--path", required=True)

    areas_parser = subparsers.add_parser("areas", help="List available areas for a catalogue path")
    areas_parser.add_argument("page")
    areas_parser.add_argument("--path", required=True)
    areas_parser.add_argument("--series")

    dates_parser = subparsers.add_parser("dates", help="Show date metadata for a catalogue path")
    dates_parser.add_argument("page")
    dates_parser.add_argument("--path", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch table data")
    fetch_parser.add_argument("page")
    fetch_parser.add_argument("--path", required=True)
    fetch_parser.add_argument("--series")
    fetch_parser.add_argument("--areas")
    fetch_parser.add_argument("--dts")
    fetch_parser.add_argument("--sequence", default="area", choices=["area", "date", "target"])
    fetch_parser.add_argument("--format", default="records", choices=["records", "matrix", "raw"])
    fetch_parser.add_argument("--as-df", action="store_true")
    fetch_parser.add_argument("--output")

    args = parser.parse_args()
    client = NBSFetcher()

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

    _dump_result(result, getattr(args, "output", None))


if __name__ == "__main__":
    main()
