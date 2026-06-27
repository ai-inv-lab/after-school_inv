from pathlib import Path
from zipfile import ZipFile

import pytest

from xbrl_financial_compare.cli import main
from xbrl_financial_compare.html_report import write_html_report
from xbrl_financial_compare.metrics import records_to_metrics
from xbrl_financial_compare.model import FinancialRecord
from xbrl_financial_compare.sample_data import SAMPLE_RECORDS, write_sample_records
from xbrl_financial_compare.xbrl_loader import extract_record_from_zip


def test_records_to_metrics_has_expected_columns():
    df = records_to_metrics(SAMPLE_RECORDS)

    assert len(df) == 3
    assert "operating_margin_pct" in df.columns
    assert float(df.loc[df["ticker"] == "6526", "operating_margin_pct"].iloc[0]) > 0


def test_write_sample_records(tmp_path: Path):
    paths = write_sample_records(tmp_path)

    assert len(paths) == 3
    assert all(path.exists() for path in paths)


def test_extract_record_reads_company_and_ticker_from_zip(tmp_path: Path):
    zip_path = tmp_path / "edinet.zip"
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <xbrl>
      <jpdei_cor:FilerNameInJapaneseDEI>ソシオネクスト</jpdei_cor:FilerNameInJapaneseDEI>
      <jpdei_cor:SecurityCodeDEI>65260</jpdei_cor:SecurityCodeDEI>
      <jpdei_cor:CurrentFiscalYearEndDateDEI>2025-03-31</jpdei_cor:CurrentFiscalYearEndDateDEI>
      <jppfs_cor:NetSales>221200000000</jppfs_cor:NetSales>
    </xbrl>
    """
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("PublicDoc/test.xbrl", xml)

    record = extract_record_from_zip(zip_path)

    assert record.company == "ソシオネクスト"
    assert record.ticker == "6526"
    assert record.period_end == "2025-03-31"


def test_extract_record_rejects_unsafe_zip_paths(tmp_path: Path):
    zip_path = tmp_path / "unsafe.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("../evil.xbrl", "<xbrl />")

    with pytest.raises(ValueError, match="Unsafe zip member path"):
        extract_record_from_zip(zip_path)


def test_compare_zips_command_extracts_and_compares(tmp_path: Path):
    zips = [
        _write_zip(tmp_path, "socionext.zip", "ソシオネクスト", "65260", 221_200_000_000, 30_900_000_000),
        _write_zip(tmp_path, "megachips.zip", "メガチップス", "68750", 72_400_000_000, 6_800_000_000),
    ]
    out_dir = tmp_path / "outputs"

    status = main(["compare-zips", *(str(path) for path in zips), "--out", str(out_dir)])

    assert status == 0
    assert (out_dir / "processed" / "6526.json").exists()
    assert (out_dir / "processed" / "6875.json").exists()
    assert (out_dir / "comparison_metrics.csv").exists()
    report = out_dir / "report.html"
    assert report.exists()
    report_text = report.read_text(encoding="utf-8")
    assert "PL比較" in report_text
    assert "QName" in report_text


def test_compare_command_expands_glob_patterns(tmp_path: Path):
    processed_dir = tmp_path / "processed"
    write_sample_records(processed_dir)
    out_dir = tmp_path / "sample"

    status = main(["compare", str(processed_dir / "*.json"), "--out", str(out_dir)])

    assert status == 0
    assert (out_dir / "comparison_metrics.csv").exists()
    assert (out_dir / "report.html").exists()


def test_html_report_embeds_context_evidence(tmp_path: Path):
    record = FinancialRecord(
        ticker="6526",
        company="ソシオネクスト",
        period_end="2025-03-31",
        source_file="socionext.zip",
        values={"net_sales": 188_535_000_000, "previous_net_sales": 221_246_000_000},
        facts={
            "net_sales": {
                "current": {
                    "value": 188_535_000_000,
                    "concept_name": "NetSales",
                    "concept_qname": "{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}NetSales",
                    "context_id": "CurrentYearDuration",
                    "period": "2024-04-012025-03-31",
                    "dimensions": [],
                    "source": "arelle",
                },
                "previous": {
                    "value": 221_246_000_000,
                    "concept_name": "NetSales",
                    "concept_qname": "{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}NetSales",
                    "context_id": "Prior1YearDuration",
                    "period": "2023-04-012024-03-31",
                    "dimensions": [],
                    "source": "arelle",
                },
            }
        },
        text_blocks={
            "description_of_business": {
                "label": "主力ビジネス",
                "text": "SoC製品の設計、開発および販売を行っています。" + "追加説明。" * 90,
                "concept_name": "DescriptionOfBusinessTextBlock",
                "concept_qname": "{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}DescriptionOfBusinessTextBlock",
                "context_id": "FilingDateInstant",
                "period": "2025-06-20",
                "dimensions": [],
                "source": "arelle",
            }
        },
    )
    df = records_to_metrics([record])
    report_path = write_html_report([record], df, tmp_path / "report.html")
    text = report_path.read_text(encoding="utf-8")

    assert "CurrentYearDuration" in text
    assert "Prior1YearDuration" in text
    assert "{http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor}NetSales" in text
    assert "Dimension" not in text
    assert "文章項目比較" in text
    assert "DescriptionOfBusinessTextBlock" in text
    assert "SoC製品の設計" in text
    assert "全文を開く" in text
    assert "data-text=" in text
    assert "window.open" in text


def test_html_report_draws_negative_bars_to_left(tmp_path: Path):
    records = [
        FinancialRecord(
            ticker="6526",
            company="ソシオネクスト",
            period_end="2025-03-31",
            source_file="socionext.zip",
            values={"net_sales": 100, "previous_net_sales": 200},
        ),
        FinancialRecord(
            ticker="6875",
            company="メガチップス",
            period_end="2025-03-31",
            source_file="megachips.zip",
            values={"net_sales": 200, "previous_net_sales": 100},
        ),
    ]
    df = records_to_metrics(records)

    report_path = write_html_report(records, df, tmp_path / "report.html")
    text = report_path.read_text(encoding="utf-8")

    assert "bar negative" in text
    assert "bar positive" in text
    assert "left:25.00%; width:25.00%" in text
    assert "left:50%; width:50.00%" in text


def _write_zip(tmp_path: Path, filename: str, company: str, ticker: str, sales: int, operating_income: int) -> Path:
    zip_path = tmp_path / filename
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <xbrl>
      <jpdei_cor:FilerNameInJapaneseDEI>{company}</jpdei_cor:FilerNameInJapaneseDEI>
      <jpdei_cor:SecurityCodeDEI>{ticker}</jpdei_cor:SecurityCodeDEI>
      <jpdei_cor:CurrentFiscalYearEndDateDEI>2025-03-31</jpdei_cor:CurrentFiscalYearEndDateDEI>
      <jppfs_cor:NetSales>{sales}</jppfs_cor:NetSales>
      <jppfs_cor:OperatingIncome>{operating_income}</jppfs_cor:OperatingIncome>
    </xbrl>
    """
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("PublicDoc/test.xbrl", xml)
    return zip_path
