from __future__ import annotations

import re
from pathlib import Path
from zipfile import ZipFile

import tempfile
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from .model import FinancialRecord


CONCEPT_ALIASES = {
    "net_sales": [
        "NetSales",
        "Sales",
        "OperatingRevenue",
        "Revenue",
    ],
    "operating_income": [
        "OperatingIncome",
        "OperatingProfit",
    ],
    "profit": [
        "ProfitLoss",
        "ProfitAttributableToOwnersOfParent",
        "NetIncome",
    ],
    "total_assets": [
        "Assets",
        "TotalAssets",
    ],
    "equity": [
        "NetAssets",
        "Equity",
        "EquityAttributableToOwnersOfParent",
    ],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "CashFlowsFromOperatingActivities",
    ],
    "investing_cash_flow": [
        "NetCashProvidedByUsedInInvestingActivities",
        "CashFlowsFromInvestingActivities",
    ],
    "research_and_development_expenses": [
        "ResearchAndDevelopmentExpenses",
        "ResearchAndDevelopmentExpense",
        "ResearchAndDevelopmentExpensesResearchAndDevelopmentActivities",
        "ResearchAndDevelopmentExpensesSGA",
        "ResearchAndDevelopmentExpensesIncludedInGeneralAndAdministrativeExpensesAndManufacturingCostForCurrentPeriod",
    ],
}

PL_METRICS = {"net_sales", "operating_income", "profit"}
BS_METRICS = {"total_assets", "equity"}
CF_METRICS = {"operating_cash_flow", "investing_cash_flow"}
DURATION_METRICS = PL_METRICS | CF_METRICS | {"research_and_development_expenses"}

TEXT_BLOCKS = {
    "description_of_business": {
        "label": "主力ビジネス",
        "concepts": ["DescriptionOfBusinessTextBlock"],
    },
    "business_environment": {
        "label": "経営環境・対処すべき課題",
        "concepts": ["BusinessPolicyBusinessEnvironmentIssuesToAddressEtcTextBlock"],
    },
    "management_analysis": {
        "label": "業績・財政状態の説明",
        "concepts": ["ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"],
    },
}


def extract_record_from_zip(
    zip_path: Path,
    *,
    ticker: str = "",
    company: str = "",
    period_end: str = "",
) -> FinancialRecord:
    notes: list[str] = []
    metadata = _extract_metadata(zip_path, notes)
    ticker = ticker or metadata.get("ticker") or zip_path.stem
    company = company or metadata.get("company") or zip_path.stem
    period_end = period_end or metadata.get("period_end") or ""
    values, labels, facts, text_blocks = _extract_with_arelle(zip_path, notes)
    if not any(value is not None for value in values.values()):
        fallback_values, fallback_labels, fallback_facts, fallback_text_blocks = _extract_with_xml_scan(zip_path, notes)
        values.update({key: value for key, value in fallback_values.items() if values.get(key) is None and value is not None})
        labels.update(fallback_labels)
        facts.update(fallback_facts)
        text_blocks.update({key: value for key, value in fallback_text_blocks.items() if key not in text_blocks})
    if not period_end:
        period_end = _guess_period_end(zip_path) or "unknown"
    return FinancialRecord(
        ticker=ticker,
        company=company,
        period_end=period_end,
        source_file=str(zip_path),
        values=values,
        labels=labels,
        facts=facts,
        text_blocks=text_blocks,
        notes=notes,
    )


def _extract_metadata(zip_path: Path, notes: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    company_tags = {
        "FilerNameInJapaneseDEI",
        "FilerNameInEnglishDEI",
        "CompanyNameCoverPage",
        "CompanyName",
        "CompanyNameInJapanese",
    }
    ticker_tags = {
        "SecurityCodeDEI",
        "SecuritiesCodeDEI",
        "SecurityCode",
        "SecuritiesCode",
    }
    period_tags = {
        "CurrentFiscalYearEndDateDEI",
        "CurrentPeriodEndDateDEI",
        "PeriodEndDate",
    }
    with ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith((".xbrl", ".xml", ".htm", ".html")):
                continue
            try:
                text = archive.read(name).decode("utf-8", errors="ignore")
            except Exception:
                continue
            soup = BeautifulSoup(text, "xml")
            for tag in soup.find_all():
                local_name = str(tag.name).split(":")[-1]
                value = tag.text.strip()
                if not value:
                    continue
                if "company" not in metadata and local_name in company_tags:
                    metadata["company"] = value
                elif "ticker" not in metadata and local_name in ticker_tags:
                    metadata["ticker"] = _normalize_ticker(value)
                elif "period_end" not in metadata and local_name in period_tags:
                    metadata["period_end"] = value
                if {"company", "ticker", "period_end"} <= set(metadata):
                    notes.append("XBRL zip内の提出者情報から会社名、証券コード、期末日を取得しました。")
                    return metadata
    if metadata:
        notes.append("XBRL zip内の提出者情報から一部のメタデータを取得しました。")
    return metadata


def _extract_with_arelle(
    zip_path: Path,
    notes: list[str],
) -> tuple[dict[str, float | None], dict[str, str], dict[str, dict], dict[str, dict]]:
    values = {key: None for key in CONCEPT_ALIASES}
    labels: dict[str, str] = {}
    facts: dict[str, dict] = {}
    text_blocks: dict[str, dict] = {}
    try:
        from arelle import Cntlr
    except Exception as exc:
        notes.append(f"Arelleを読み込めませんでした: {type(exc).__name__}: {exc}")
        return values, labels, facts, text_blocks

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        with ZipFile(zip_path) as archive:
            archive.extractall(tmp_dir)
        entry = _find_entrypoint(tmp_dir)
        if entry is None:
            notes.append("XBRLの入口ファイルを見つけられませんでした。")
            return values, labels, facts, text_blocks
        controller = Cntlr.Cntlr(logFileName=None)
        try:
            model_xbrl = controller.modelManager.load(str(entry))
            for fact in model_xbrl.facts:
                local_name = getattr(fact.concept.qname, "localName", "")
                text_block_key = _text_block_for_concept(local_name)
                if text_block_key and text_block_key not in text_blocks:
                    block = _text_block_evidence(fact, local_name)
                    if block:
                        text_blocks[text_block_key] = block
                metric = _metric_for_concept(local_name)
                if not metric:
                    continue
                context = getattr(fact, "context", None)
                period_key = _period_key_for_metric(metric, context)
                if period_key is None:
                    continue
                number = _fact_number(getattr(fact, "value", None))
                if number is None:
                    continue
                facts.setdefault(metric, {})
                if period_key not in facts[metric]:
                    facts[metric][period_key] = _fact_evidence(fact, local_name, number)
                if period_key == "current" and values.get(metric) is None:
                    values[metric] = number
                    labels[metric] = local_name
                if period_key == "previous":
                    previous_key = f"previous_{metric}"
                    if values.get(previous_key) is None:
                        values[previous_key] = number
                        labels[previous_key] = local_name
            model_xbrl.close()
        finally:
            controller.close()
    notes.append("ArelleでXBRLを読み込みました。")
    return values, labels, facts, text_blocks


def _extract_with_xml_scan(
    zip_path: Path,
    notes: list[str],
) -> tuple[dict[str, float | None], dict[str, str], dict[str, dict], dict[str, dict]]:
    values = {key: None for key in CONCEPT_ALIASES}
    labels: dict[str, str] = {}
    facts: dict[str, dict] = {}
    text_blocks: dict[str, dict] = {}
    with ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith((".xbrl", ".xml", ".htm", ".html")):
                continue
            try:
                text = archive.read(name).decode("utf-8", errors="ignore")
            except Exception:
                continue
            soup = BeautifulSoup(text, "xml")
            for tag in soup.find_all():
                local_name = str(tag.name).split(":")[-1]
                text_block_key = _text_block_for_concept(local_name)
                if text_block_key and text_block_key not in text_blocks:
                    cleaned = _clean_text_block(tag.text)
                    if cleaned:
                        text_blocks[text_block_key] = {
                            "label": TEXT_BLOCKS[text_block_key]["label"],
                            "text": cleaned,
                            "concept_name": local_name,
                            "concept_qname": str(tag.name),
                            "context_id": str(tag.get("contextRef", "")),
                            "period": "",
                            "dimensions": [],
                            "source": "xml_scan",
                        }
                metric = _metric_for_concept(local_name)
                if not metric or values.get(metric) is not None:
                    continue
                number = _fact_number(tag.text)
                if number is not None:
                    values[metric] = number
                    labels[metric] = str(tag.name)
                    facts.setdefault(metric, {})["current"] = {
                        "value": number,
                        "concept_name": local_name,
                        "concept_qname": str(tag.name),
                        "context_id": "",
                        "period": "",
                        "dimensions": [],
                        "source": "xml_scan",
                    }
    notes.append("Arelleで十分に読めない項目があったため、XML走査で補いました。")
    return values, labels, facts, text_blocks


def _find_entrypoint(root: Path) -> Path | None:
    candidates = sorted(
        [
            *root.rglob("*.xbrl"),
            *root.rglob("*.xhtml"),
            *root.rglob("*.htm"),
            *root.rglob("*.html"),
        ],
        key=lambda path: (0 if "PublicDoc" in path.as_posix() else 1, len(path.as_posix())),
    )
    return candidates[0] if candidates else None


def _metric_for_concept(local_name: str) -> str | None:
    compact = local_name.replace("_", "").lower()
    for metric, aliases in CONCEPT_ALIASES.items():
        for alias in aliases:
            if compact == alias.lower():
                return metric
    return None


def _text_block_for_concept(local_name: str) -> str | None:
    compact = local_name.replace("_", "").lower()
    for key, definition in TEXT_BLOCKS.items():
        for concept in definition["concepts"]:
            if compact == concept.lower():
                return key
    return None


def _period_key_for_metric(metric: str, context) -> str | None:
    if context is None:
        return None
    if getattr(context, "qnameDims", None):
        return None
    context_id = str(getattr(context, "id", "") or "")
    if metric in DURATION_METRICS:
        if context_id == "CurrentYearDuration":
            return "current"
        if context_id == "Prior1YearDuration":
            return "previous"
    if metric in BS_METRICS:
        if context_id == "CurrentYearInstant":
            return "current"
        if context_id == "Prior1YearInstant":
            return "previous"
    return None


def _fact_evidence(fact, concept_name: str, value: float) -> dict:
    context = fact.context
    period = getattr(context, "period", None)
    concept_qname = getattr(getattr(fact, "concept", None), "qname", None)
    return {
        "value": value,
        "concept_name": concept_name,
        "concept_qname": str(concept_qname or concept_name),
        "context_id": str(getattr(context, "id", "") or ""),
        "period": getattr(period, "stringValue", "") if period is not None else "",
        "dimensions": [str(key) for key in (getattr(context, "qnameDims", {}) or {}).keys()],
        "source": "arelle",
    }


def _text_block_evidence(fact, concept_name: str) -> dict | None:
    context = getattr(fact, "context", None)
    if context is None or getattr(context, "qnameDims", None):
        return None
    text = _clean_text_block(getattr(fact, "value", None))
    if not text:
        return None
    period = getattr(context, "period", None)
    key = _text_block_for_concept(concept_name)
    concept_qname = getattr(getattr(fact, "concept", None), "qname", None)
    return {
        "label": TEXT_BLOCKS[key]["label"] if key else concept_name,
        "text": text,
        "concept_name": concept_name,
        "concept_qname": str(concept_qname or concept_name),
        "context_id": str(getattr(context, "id", "") or ""),
        "period": getattr(period, "stringValue", "") if period is not None else "",
        "dimensions": [str(dim_key) for dim_key in (getattr(context, "qnameDims", {}) or {}).keys()],
        "source": "arelle",
    }


def _clean_text_block(value: object) -> str:
    soup = BeautifulSoup(str(value or ""), "html.parser")
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _fact_number(value: object) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_ticker(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) >= 4:
        return digits[:4]
    return value.strip()


def _guess_period_end(zip_path: Path) -> str | None:
    with ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith((".xbrl", ".xml", ".htm", ".html")):
                continue
            try:
                root = ET.fromstring(archive.read(name))
            except Exception:
                continue
            for elem in root.iter():
                if elem.tag.endswith("endDate") and elem.text:
                    return elem.text.strip()
    return None
