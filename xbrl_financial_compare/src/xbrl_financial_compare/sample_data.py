from __future__ import annotations

from pathlib import Path

from .model import FinancialRecord, save_record


def _facts(values: dict[str, float | None]) -> dict:
    facts: dict[str, dict] = {}
    for metric, concept in [
        ("net_sales", "NetSales"),
        ("operating_income", "OperatingIncome"),
        ("profit", "ProfitLoss"),
        ("research_and_development_expenses", "ResearchAndDevelopmentExpensesSGA"),
        ("total_assets", "Assets"),
        ("equity", "NetAssets"),
        ("operating_cash_flow", "NetCashProvidedByUsedInOperatingActivities"),
        ("investing_cash_flow", "NetCashProvidedByUsedInInvestmentActivities"),
    ]:
        current = values.get(metric)
        previous = values.get(f"previous_{metric}")
        facts[metric] = {}
        if current is not None:
            facts[metric]["current"] = {
                "value": current,
                "concept_name": concept,
                "concept_qname": f"{{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}}{concept}",
                "context_id": "CurrentYearInstant" if metric in {"total_assets", "equity"} else "CurrentYearDuration",
                "period": "sample-current-year",
                "dimensions": [],
                "source": "sample",
            }
        if previous is not None:
            facts[metric]["previous"] = {
                "value": previous,
                "concept_name": concept,
                "concept_qname": f"{{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}}{concept}",
                "context_id": "Prior1YearInstant" if metric in {"total_assets", "equity"} else "Prior1YearDuration",
                "period": "sample-prior-year",
                "dimensions": [],
                "source": "sample",
            }
    return facts


def _text_blocks(company: str, business: str, environment: str, analysis: str) -> dict:
    namespace = "http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor"
    return {
        "description_of_business": {
            "label": "事業の内容",
            "text": business,
            "concept_qname": f"{{{namespace}}}DescriptionOfBusinessTextBlock",
            "context_id": "FilingDateInstant",
            "period": "sample-filing-date",
            "source": "sample",
        },
        "business_environment": {
            "label": "経営方針、経営環境及び対処すべき課題等",
            "text": environment,
            "concept_qname": f"{{{namespace}}}BusinessPolicyBusinessEnvironmentIssuesToAddressEtcTextBlock",
            "context_id": "FilingDateInstant",
            "period": "sample-filing-date",
            "source": "sample",
        },
        "management_analysis": {
            "label": "経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析",
            "text": analysis,
            "concept_qname": f"{{{namespace}}}ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock",
            "context_id": "FilingDateInstant",
            "period": "sample-filing-date",
            "source": "sample",
        },
    }


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
            "previous_operating_income": 26_400_000_000,
            "profit": 22_800_000_000,
            "previous_profit": 19_700_000_000,
            "total_assets": 276_000_000_000,
            "previous_total_assets": 251_000_000_000,
            "equity": 150_000_000_000,
            "previous_equity": 132_000_000_000,
            "operating_cash_flow": 18_300_000_000,
            "previous_operating_cash_flow": 16_500_000_000,
            "investing_cash_flow": -8_700_000_000,
            "previous_investing_cash_flow": -7_900_000_000,
            "research_and_development_expenses": 33_400_000_000,
            "previous_research_and_development_expenses": 28_200_000_000,
        },
        facts=_facts(
            {
                "net_sales": 221_200_000_000,
                "previous_net_sales": 192_800_000_000,
                "operating_income": 30_900_000_000,
                "previous_operating_income": 26_400_000_000,
                "profit": 22_800_000_000,
                "previous_profit": 19_700_000_000,
                "total_assets": 276_000_000_000,
                "previous_total_assets": 251_000_000_000,
                "equity": 150_000_000_000,
                "previous_equity": 132_000_000_000,
                "operating_cash_flow": 18_300_000_000,
                "previous_operating_cash_flow": 16_500_000_000,
                "investing_cash_flow": -8_700_000_000,
                "previous_investing_cash_flow": -7_900_000_000,
                "research_and_development_expenses": 33_400_000_000,
                "previous_research_and_development_expenses": 28_200_000_000,
            }
        ),
        text_blocks=_text_blocks(
            "ソシオネクスト",
            "ソシオネクストは、SoC製品の設計、開発および販売を主な事業とするファブレス半導体企業です。画像処理、ネットワーク、車載、データセンターなどの用途に向け、顧客ごとの仕様に合わせた半導体を提供する想定のサンプル文章です。",
            "先端プロセスの開発費、設計人材の確保、顧客の投資サイクルが重要な経営課題です。需要の山谷が大きいため、研究開発投資と受注見通しのバランスを継続的に確認する必要がある、という読み方を示すサンプルです。",
            "売上高は前年度から増加し、営業利益率も改善しています。一方で研究開発費の水準が高く、将来の製品投入に向けた先行投資が利益率にどう効くかを見る必要があります。これはXBRLの文章項目比較用に作成したサンプルです。",
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
            "previous_operating_income": 7_300_000_000,
            "profit": 8_500_000_000,
            "previous_profit": 6_900_000_000,
            "total_assets": 122_000_000_000,
            "previous_total_assets": 118_000_000_000,
            "equity": 86_000_000_000,
            "previous_equity": 80_000_000_000,
            "operating_cash_flow": 9_800_000_000,
            "previous_operating_cash_flow": 8_900_000_000,
            "investing_cash_flow": -3_200_000_000,
            "previous_investing_cash_flow": -4_200_000_000,
            "research_and_development_expenses": 12_700_000_000,
            "previous_research_and_development_expenses": 11_800_000_000,
        },
        facts=_facts(
            {
                "net_sales": 72_400_000_000,
                "previous_net_sales": 67_900_000_000,
                "operating_income": 6_800_000_000,
                "previous_operating_income": 7_300_000_000,
                "profit": 8_500_000_000,
                "previous_profit": 6_900_000_000,
                "total_assets": 122_000_000_000,
                "previous_total_assets": 118_000_000_000,
                "equity": 86_000_000_000,
                "previous_equity": 80_000_000_000,
                "operating_cash_flow": 9_800_000_000,
                "previous_operating_cash_flow": 8_900_000_000,
                "investing_cash_flow": -3_200_000_000,
                "previous_investing_cash_flow": -4_200_000_000,
                "research_and_development_expenses": 12_700_000_000,
                "previous_research_and_development_expenses": 11_800_000_000,
            }
        ),
        text_blocks=_text_blocks(
            "メガチップス",
            "メガチップスは、特定用途向けLSIやシステム製品を扱う半導体関連企業です。ゲーム、通信、産業機器などの顧客分野に向けた製品開発と販売を行う想定のサンプル文章です。",
            "顧客別の需要変動、在庫調整、為替、開発案件の採算が業績に影響します。自社の強みをどの用途に集中させるか、研究開発費をどの程度維持するかが比較ポイントになります。",
            "売上高は緩やかに増えていますが、営業利益はやや弱含みです。営業外・特別項目を含む純利益との違いを確認し、PLのどこで変化が起きたかを見るためのサンプルです。",
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
            "previous_operating_income": -120_000_000,
            "profit": 520_000_000,
            "previous_profit": -260_000_000,
            "total_assets": 15_400_000_000,
            "previous_total_assets": 14_900_000_000,
            "equity": 12_700_000_000,
            "previous_equity": 12_100_000_000,
            "operating_cash_flow": 760_000_000,
            "previous_operating_cash_flow": -180_000_000,
            "investing_cash_flow": -210_000_000,
            "previous_investing_cash_flow": -330_000_000,
            "research_and_development_expenses": 1_120_000_000,
            "previous_research_and_development_expenses": 1_040_000_000,
        },
        facts=_facts(
            {
                "net_sales": 5_900_000_000,
                "previous_net_sales": 5_300_000_000,
                "operating_income": 410_000_000,
                "previous_operating_income": -120_000_000,
                "profit": 520_000_000,
                "previous_profit": -260_000_000,
                "total_assets": 15_400_000_000,
                "previous_total_assets": 14_900_000_000,
                "equity": 12_700_000_000,
                "previous_equity": 12_100_000_000,
                "operating_cash_flow": 760_000_000,
                "previous_operating_cash_flow": -180_000_000,
                "investing_cash_flow": -210_000_000,
                "previous_investing_cash_flow": -330_000_000,
                "research_and_development_expenses": 1_120_000_000,
                "previous_research_and_development_expenses": 1_040_000_000,
            }
        ),
        text_blocks=_text_blocks(
            "ザインエレクトロニクス",
            "ザインエレクトロニクスは、高速インターフェースや画像処理関連の半導体製品を扱う企業です。規模は比較的小さいものの、特定技術に集中して製品展開する想定のサンプル文章です。",
            "中小型の半導体企業では、売上規模に対する研究開発費の比率、特定顧客・特定製品への依存、黒字化の持続性が重要です。大企業と同じ物差しだけでなく、変化率も見ます。",
            "前年度の赤字から黒字に転じた想定です。利益率の改善だけでなく、営業キャッシュ・フローがプラスに戻っているか、研究開発を削りすぎていないかを並べて確認するサンプルです。",
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
