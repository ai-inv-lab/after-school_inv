from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

from .model import FinancialRecord


PL_ROWS = [
    ("net_sales", "売上高"),
    ("operating_income", "営業利益"),
    ("profit", "当期純利益"),
    ("research_and_development_expenses", "研究開発費"),
]

TEXT_BLOCK_ROWS = [
    ("description_of_business", "主力ビジネス"),
    ("business_environment", "経営環境・対処すべき課題"),
    ("management_analysis", "業績・財政状態の説明"),
]

GRAPH_ROWS = [
    ("sales_growth_pct", "売上高成長率"),
    ("operating_margin_pct", "営業利益率"),
    ("roe_pct", "ROE"),
    ("equity_ratio_pct", "自己資本比率"),
    ("rd_ratio_pct", "研究開発費率"),
]


def write_html_report(records: list[FinancialRecord], metrics_df: pd.DataFrame, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"ja\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "<title>EDINET XBRL 財務比較レポート</title>",
            "<style>",
            _css(),
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<h1>EDINET XBRL 財務比較レポート</h1>",
            "<p class=\"lead\">EDINETからダウンロードしたXBRL zipをArelleで読み込み、連結のBS/PL/CFと文章項目を比較しています。</p>",
            _render_sample_notice(records),
            _render_summary(records),
            "<h2>PL比較</h2>",
            _render_pl_table(records),
            "<h2>主要指標</h2>",
            _render_metric_bars(metrics_df),
            "<h2>文章項目比較</h2>",
            _render_text_blocks(records),
            "<h2>エビデンス</h2>",
            _render_evidence(records),
            "</main>",
            "<script>",
            _script(),
            "</script>",
            "</body>",
            "</html>",
        ]
    )
    out_path.write_text(html + "\n", encoding="utf-8")
    return out_path


def _render_summary(records: list[FinancialRecord]) -> str:
    rows = []
    for record in records:
        rows.append(
            "<tr>"
            f"<td>{escape(record.ticker)}</td>"
            f"<td>{escape(record.company)}</td>"
            f"<td>{escape(record.period_end)}</td>"
            f"<td>{escape(Path(record.source_file).name)}</td>"
            "</tr>"
        )
    return (
        "<h2>対象書類</h2>"
        "<table><thead><tr><th>コード</th><th>会社名</th><th>期末日</th><th>元zip</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _render_sample_notice(records: list[FinancialRecord]) -> str:
    if not records or any(record.source_file != "sample" for record in records):
        return ""
    return (
        "<p class=\"notice\">"
        "このレポートはプログラムの動作説明用サンプルです。実在する会社名と証券コードを題材にしていますが、"
        "数値と文章は架空データであり、実際の有価証券報告書の値ではありません。"
        "</p>"
    )


def _render_pl_table(records: list[FinancialRecord]) -> str:
    header = "".join(f"<th>{escape(record.ticker)}<br>{escape(record.company)}</th>" for record in records)
    rows = []
    for metric, label in PL_ROWS:
        current_cells = []
        previous_cells = []
        growth_cells = []
        for record in records:
            current = _fact_value(record, metric, "current")
            previous = _fact_value(record, metric, "previous")
            current_cells.append(f"<td>{_yen(current)}</td>")
            previous_cells.append(f"<td>{_yen(previous)}</td>")
            growth_cells.append(f"<td>{_growth(current, previous)}</td>")
        rows.append(f"<tr><th>{label}<br><span>今年度</span></th>{''.join(current_cells)}</tr>")
        rows.append(f"<tr><th>{label}<br><span>前年度</span></th>{''.join(previous_cells)}</tr>")
        rows.append(f"<tr class=\"sub\"><th>{label}<br><span>前年比</span></th>{''.join(growth_cells)}</tr>")
    return f"<table><thead><tr><th>項目</th>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _render_metric_bars(df: pd.DataFrame) -> str:
    sections = []
    for column, label in GRAPH_ROWS:
        values = [(str(row["ticker"]), _num(row.get(column))) for _, row in df.iterrows()]
        max_abs = max([abs(value or 0) for _, value in values] + [1])
        bars = []
        for ticker, value in values:
            width = abs(value or 0) / max_abs * 50
            klass = "negative" if (value or 0) < 0 else "positive"
            if (value or 0) < 0:
                position = f"left:{50 - width:.2f}%; width:{width:.2f}%"
            else:
                position = f"left:50%; width:{width:.2f}%"
            bars.append(
                "<div class=\"bar-row\">"
                f"<div class=\"bar-label\">{escape(ticker)}</div>"
                "<div class=\"bar-track\">"
                f"<div class=\"bar {klass}\" style=\"{position}\"></div>"
                "</div>"
                f"<div class=\"bar-value\">{_pct(value)}</div>"
                "</div>"
            )
        sections.append(f"<section class=\"metric\"><h3>{label}</h3>{''.join(bars)}</section>")
    return "<div class=\"metrics\">" + "".join(sections) + "</div>"


def _render_text_blocks(records: list[FinancialRecord]) -> str:
    sections = []
    for key, label in TEXT_BLOCK_ROWS:
        cards = []
        for record in records:
            block = record.text_blocks.get(key, {})
            text = str(block.get("text", "") or "")
            title = f"{record.ticker} {record.company} - {label}"
            button = ""
            if text:
                button = (
                    "<button class=\"text-open\" type=\"button\""
                    f" data-title=\"{escape(title, quote=True)}\""
                    f" data-text=\"{escape(text, quote=True)}\">全文を開く</button>"
                )
            cards.append(
                "<article class=\"text-card\">"
                f"<h4>{escape(record.ticker)} {escape(record.company)}</h4>"
                f"<p>{escape(_excerpt(text)) if text else '-'}</p>"
                f"{button}"
                "<dl>"
                f"<dt>QName</dt><dd><code>{escape(str(block.get('concept_qname', '') or '-'))}</code></dd>"
                f"<dt>コンテキストID</dt><dd><code>{escape(str(block.get('context_id', '') or '-'))}</code></dd>"
                "</dl>"
                "</article>"
            )
        sections.append(
            "<section class=\"text-block-section\">"
            f"<h3>{escape(label)}</h3>"
            f"<div class=\"text-grid\">{''.join(cards)}</div>"
            "</section>"
        )
    return "".join(sections)


def _render_evidence(records: list[FinancialRecord]) -> str:
    rows = []
    for record in records:
        for metric, label in PL_ROWS + [("total_assets", "総資産"), ("equity", "純資産"), ("operating_cash_flow", "営業CF")]:
            for period_key, period_label in [("current", "今年度"), ("previous", "前年度")]:
                fact = record.facts.get(metric, {}).get(period_key)
                if not fact:
                    continue
                rows.append(
                    "<tr>"
                    f"<td>{escape(record.ticker)}</td>"
                    f"<td>{escape(label)}</td>"
                    f"<td>{period_label}</td>"
                    f"<td>{_yen(_num(fact.get('value')))}</td>"
                    f"<td><code>{escape(str(fact.get('concept_qname', fact.get('concept_name', ''))))}</code></td>"
                    f"<td><code>{escape(str(fact.get('context_id', '')))}</code></td>"
                    f"<td>{escape(str(fact.get('period', '')))}</td>"
                    "</tr>"
                )
    return (
        "<table class=\"evidence\"><thead><tr><th>コード</th><th>項目</th><th>年度</th><th>値</th>"
        "<th>QName</th><th>コンテキストID</th><th>期間</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _fact_value(record: FinancialRecord, metric: str, period_key: str) -> float | None:
    fact = record.facts.get(metric, {}).get(period_key)
    return _num(fact.get("value")) if fact else None


def _num(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _yen(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value / 100_000_000:,.2f} 億円"


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}%"


def _growth(current: float | None, previous: float | None) -> str:
    if current is None or previous in (None, 0):
        return "-"
    return _pct((current / previous - 1) * 100)


def _excerpt(text: str, limit: int = 520) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _css() -> str:
    return """
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif; color: #20242a; background: #f6f7f9; }
main { max-width: 1120px; margin: 0 auto; padding: 32px 20px 56px; }
h1 { margin: 0 0 8px; font-size: 30px; }
h2 { margin-top: 34px; border-bottom: 2px solid #d7dce3; padding-bottom: 8px; }
h3 { margin: 0 0 12px; font-size: 17px; }
.lead { color: #4c5563; }
.notice { border: 1px solid #d7b46a; background: #fff7df; color: #60420b; padding: 12px 14px; margin: 18px 0 22px; }
table { width: 100%; border-collapse: collapse; background: white; margin: 14px 0 24px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
th, td { border: 1px solid #dfe3e8; padding: 9px 10px; text-align: right; vertical-align: top; }
th { background: #eef2f6; font-weight: 700; }
td:first-child, th:first-child { text-align: left; }
th span { color: #6b7280; font-size: 12px; font-weight: 500; }
tr.sub th, tr.sub td { background: #fbfcfe; color: #374151; }
.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.metric { background: white; border: 1px solid #dfe3e8; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.bar-row { display: grid; grid-template-columns: 58px 1fr 86px; gap: 10px; align-items: center; margin: 10px 0; }
.bar-label { font-weight: 700; }
.bar-track { position: relative; height: 18px; background: #edf1f5; border-radius: 4px; overflow: hidden; }
.bar-track::before { content: ""; position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: #8c97a6; }
.bar { position: absolute; top: 0; height: 100%; min-width: 2px; }
.positive { background: #4777c2; }
.negative { background: #c84b4b; }
.bar-value { text-align: right; font-variant-numeric: tabular-nums; }
.text-block-section { margin: 18px 0 26px; }
.text-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
.text-card { background: white; border: 1px solid #dfe3e8; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.text-card h4 { margin: 0 0 10px; font-size: 15px; }
.text-card p { margin: 0 0 12px; line-height: 1.7; color: #303946; }
.text-open { appearance: none; border: 1px solid #bac4d1; background: #f7f9fc; color: #1f2937; border-radius: 4px; padding: 6px 10px; margin: 0 0 12px; font: inherit; font-size: 13px; cursor: pointer; }
.text-open:hover { background: #eaf0f7; border-color: #8fa0b6; }
.text-card dl { display: grid; grid-template-columns: 92px 1fr; gap: 4px 8px; margin: 0; color: #5b6472; font-size: 12px; }
.text-card dt { font-weight: 700; }
.text-card dd { margin: 0; overflow-wrap: anywhere; }
.evidence { font-size: 13px; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
@media (max-width: 760px) { table { display: block; overflow-x: auto; } .bar-row { grid-template-columns: 52px 1fr 74px; } }
"""


def _script() -> str:
    return """
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, function(ch) {
    return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch];
  });
}

document.querySelectorAll('.text-open').forEach(function(button) {
  button.addEventListener('click', function() {
    const title = button.dataset.title || '文章項目';
    const text = button.dataset.text || '';
    const page = [
      '<!doctype html>',
      '<html lang="ja">',
      '<head>',
      '<meta charset="utf-8">',
      '<meta name="viewport" content="width=device-width, initial-scale=1">',
      '<title>' + escapeHtml(title) + '</title>',
      '<style>',
      'body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic",sans-serif;color:#20242a;background:#f6f7f9;}',
      'main{max-width:920px;margin:0 auto;padding:28px 20px 48px;}',
      'h1{font-size:24px;margin:0 0 18px;}',
      'div{white-space:pre-wrap;line-height:1.85;background:white;border:1px solid #dfe3e8;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.06);}',
      '</style>',
      '</head>',
      '<body><main><h1>' + escapeHtml(title) + '</h1><div>' + escapeHtml(text) + '</div></main></body>',
      '</html>'
    ].join('');
    const blob = new Blob([page], {type: 'text/html'});
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank', 'width=980,height=760');
    setTimeout(function() { URL.revokeObjectURL(url); }, 60000);
  });
});
"""
