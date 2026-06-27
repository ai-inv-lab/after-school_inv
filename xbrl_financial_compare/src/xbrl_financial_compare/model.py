from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import json


@dataclass
class FinancialRecord:
    ticker: str
    company: str
    period_end: str
    source_file: str
    accounting_standard: str = "日本基準"
    consolidated: bool = True
    values: dict[str, float | None] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    facts: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    text_blocks: dict[str, dict[str, Any]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialRecord":
        return cls(
            ticker=str(data.get("ticker", "")),
            company=str(data.get("company", "")),
            period_end=str(data.get("period_end", "")),
            source_file=str(data.get("source_file", "")),
            accounting_standard=str(data.get("accounting_standard", "日本基準")),
            consolidated=bool(data.get("consolidated", True)),
            values=dict(data.get("values", {})),
            labels=dict(data.get("labels", {})),
            facts=dict(data.get("facts", {})),
            text_blocks=dict(data.get("text_blocks", {})),
            notes=list(data.get("notes", [])),
        )


def save_record(record: FinancialRecord, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_record(path: Path) -> FinancialRecord:
    return FinancialRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
