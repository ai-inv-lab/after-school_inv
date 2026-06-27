from __future__ import annotations

from pathlib import Path

from .model import FinancialRecord, save_record


def _facts(values: dict[str, float | None]) -> dict:
    facts: dict[str, dict] = {}
    for metric, concept in [
        ("net_sales", "NetSales"),
        ("operating_income", "OperatingIncome"),
        ("profit", "ProfitLoss"),
    ]:
        current = values.get(metric)
        previous = values.get(f"previous_{metric}") if metric != "net_sales" else values.get("previous_net_sales")
        facts[metric] = {}
        if current is not None:
            facts[metric]["current"] = {
                "value": current,
                "concept_name": concept,
                "concept_qname": f"{{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}}{concept}",
                "context_id": "CurrentYearDuration",
                "period": "sample-current-year",
                "dimensions": [],
                "source": "sample",
            }
        if previous is not None:
            facts[metric]["previous"] = {
                "value": previous,
                "concept_name": concept,
                "concept_qname": f"{{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}}{concept}",
                "context_id": "Prior1YearDuration",
                "period": "sample-prior-year",
                "dimensions": [],
                "source": "sample",
            }
    return facts


SAMPLE_RECORDS = [
    FinancialRecord(
        ticker="6526",
        company="ソシオネクスト",
        period_end="2025-03-31",
        source_file="sample",
        values={
            "net_sales": 221_200_000_000,
            "previous_net_sales": 192_800_000_000,
            "operating_income": 30_900_000_000,
            "profit": 22_800_000_000,
            "total_assets": 276_000_000_000,
            "equity": 150_000_000_000,
            "operating_cash_flow": 18_300_000_000,
            "investing_cash_flow": -8_700_000_000,
            "research_and_development_expenses": 33_400_000_000,
        },
        facts=_facts(
            {
                "net_sales": 221_200_000_000,
                "previous_net_sales": 192_800_000_000,
                "operating_income": 30_900_000_000,
                "profit": 22_800_000_000,
            }
        ),
    ),
    FinancialRecord(
        ticker="6875",
        company="メガチップス",
        period_end="2025-03-31",
        source_file="sample",
        values={
            "net_sales": 72_400_000_000,
            "previous_net_sales": 67_900_000_000,
            "operating_income": 6_800_000_000,
            "profit": 8_500_000_000,
            "total_assets": 122_000_000_000,
            "equity": 86_000_000_000,
            "operating_cash_flow": 9_800_000_000,
            "investing_cash_flow": -3_200_000_000,
            "research_and_development_expenses": 12_700_000_000,
        },
        facts=_facts(
            {
                "net_sales": 72_400_000_000,
                "previous_net_sales": 67_900_000_000,
                "operating_income": 6_800_000_000,
                "profit": 8_500_000_000,
            }
        ),
    ),
    FinancialRecord(
        ticker="6769",
        company="ザインエレクトロニクス",
        period_end="2024-12-31",
        source_file="sample",
        values={
            "net_sales": 5_900_000_000,
            "previous_net_sales": 5_300_000_000,
            "operating_income": 410_000_000,
            "profit": 520_000_000,
            "total_assets": 15_400_000_000,
            "equity": 12_700_000_000,
            "operating_cash_flow": 760_000_000,
            "investing_cash_flow": -210_000_000,
            "research_and_development_expenses": 1_120_000_000,
        },
        facts=_facts(
            {
                "net_sales": 5_900_000_000,
                "previous_net_sales": 5_300_000_000,
                "operating_income": 410_000_000,
                "profit": 520_000_000,
            }
        ),
    ),
]


def write_sample_records(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for record in SAMPLE_RECORDS:
        path = out_dir / f"sample-{record.ticker}.json"
        save_record(record, path)
        paths.append(path)
    return paths
