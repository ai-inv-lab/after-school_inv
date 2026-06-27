from __future__ import annotations

from pathlib import Path

import pandas as pd

from .model import FinancialRecord, load_record


METRIC_COLUMNS = [
    "company",
    "ticker",
    "period_end",
    "net_sales_billion_yen",
    "sales_growth_pct",
    "operating_margin_pct",
    "roe_pct",
    "equity_ratio_pct",
    "operating_cf_billion_yen",
    "free_cf_billion_yen",
    "rd_ratio_pct",
]


def records_to_metrics(records: list[FinancialRecord]) -> pd.DataFrame:
    rows = [_record_to_metrics(record) for record in records]
    return pd.DataFrame(rows, columns=METRIC_COLUMNS)


def load_records(paths: list[Path]) -> list[FinancialRecord]:
    return [load_record(path) for path in paths]


def _record_to_metrics(record: FinancialRecord) -> dict[str, float | str | None]:
    values = record.values
    net_sales = _num(values.get("net_sales"))
    previous_net_sales = _num(values.get("previous_net_sales"))
    operating_income = _num(values.get("operating_income"))
    profit = _num(values.get("profit"))
    total_assets = _num(values.get("total_assets"))
    equity = _num(values.get("equity"))
    operating_cf = _num(values.get("operating_cash_flow"))
    investing_cf = _num(values.get("investing_cash_flow"))
    rd = _num(values.get("research_and_development_expenses"))
    free_cf = None
    if operating_cf is not None and investing_cf is not None:
        free_cf = operating_cf + investing_cf
    return {
        "company": record.company,
        "ticker": record.ticker,
        "period_end": record.period_end,
        "net_sales_billion_yen": _billion(net_sales),
        "sales_growth_pct": _pct_ratio(net_sales, previous_net_sales, subtract_one=True),
        "operating_margin_pct": _pct_ratio(operating_income, net_sales),
        "roe_pct": _pct_ratio(profit, equity),
        "equity_ratio_pct": _pct_ratio(equity, total_assets),
        "operating_cf_billion_yen": _billion(operating_cf),
        "free_cf_billion_yen": _billion(free_cf),
        "rd_ratio_pct": _pct_ratio(rd, net_sales),
    }


def _num(value: float | int | str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _billion(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value / 1_000_000_000, 2)


def _pct_ratio(numerator: float | None, denominator: float | None, *, subtract_one: bool = False) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    ratio = numerator / denominator
    if subtract_one:
        ratio -= 1
    return round(ratio * 100, 2)

