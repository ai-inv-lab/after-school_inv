from __future__ import annotations

import argparse
from pathlib import Path

from .html_report import write_html_report
from .metrics import load_records, records_to_metrics
from .model import save_record
from .sample_data import write_sample_records
from .xbrl_loader import extract_record_from_zip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare financial metrics from EDINET XBRL files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample_parser = subparsers.add_parser("sample", help="write sample processed JSON files")
    sample_parser.add_argument("--out", type=Path, default=Path("data/processed"))

    extract_parser = subparsers.add_parser("extract", help="extract financial values from an EDINET XBRL zip")
    extract_parser.add_argument("--zip", type=Path, required=True, dest="zip_path")
    extract_parser.add_argument("--ticker", default="", help="optional override; normally read from the XBRL zip")
    extract_parser.add_argument("--company", default="", help="optional override; normally read from the XBRL zip")
    extract_parser.add_argument("--period-end", default="")
    extract_parser.add_argument("--out", type=Path, default=None)

    compare_parser = subparsers.add_parser("compare", help="compare processed JSON files")
    compare_parser.add_argument("inputs", type=Path, nargs="+")
    compare_parser.add_argument("--out", type=Path, default=Path("outputs"))

    compare_zips_parser = subparsers.add_parser(
        "compare-zips",
        help="extract multiple EDINET XBRL zip files and compare them in one command",
    )
    compare_zips_parser.add_argument("zips", type=Path, nargs="+")
    compare_zips_parser.add_argument("--out", type=Path, default=Path("outputs"))
    compare_zips_parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="where processed JSON files are written; default is OUT/processed",
    )

    args = parser.parse_args(argv)
    if args.command == "sample":
        paths = write_sample_records(args.out)
        for path in paths:
            print(path)
        return 0
    if args.command == "extract":
        record = extract_record_from_zip(
            args.zip_path,
            ticker=args.ticker,
            company=args.company,
            period_end=args.period_end,
        )
        out_path = args.out or Path("data/processed") / f"{record.ticker}.json"
        save_record(record, out_path)
        print(out_path)
        for note in record.notes:
            print(f"- {note}")
        return 0
    if args.command == "compare":
        csv_path, report_path = _write_comparison(load_records(args.inputs), args.out)
        print(csv_path)
        print(report_path)
        return 0
    if args.command == "compare-zips":
        records = []
        processed_dir = args.processed_dir or args.out / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        for zip_path in args.zips:
            record = extract_record_from_zip(zip_path)
            records.append(record)
            json_path = processed_dir / f"{_safe_stem(record.ticker, zip_path)}.json"
            save_record(record, json_path)
            print(json_path)
        csv_path, report_path = _write_comparison(records, args.out)
        print(csv_path)
        print(report_path)
        return 0
    return 1


def _write_comparison(records, out_dir: Path) -> tuple[Path, Path]:
    df = records_to_metrics(records)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "comparison_metrics.csv"
    report_path = out_dir / "report.html"
    df.to_csv(csv_path, index=False)
    write_html_report(records, df, report_path)
    return csv_path, report_path


def _safe_stem(ticker: str, zip_path: Path) -> str:
    stem = ticker.strip() or zip_path.stem
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in stem)


if __name__ == "__main__":
    raise SystemExit(main())
