import json
from typing import Iterable, Optional

from app.config import get_settings
from app.schemas import DocumentRecord


class ManifestStore:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _read(self) -> list[DocumentRecord]:
        raw = self.settings.manifest_path.read_text(encoding="utf-8")
        items = json.loads(raw or "[]")
        return [DocumentRecord.model_validate(item) for item in items]

    def _write(self, records: Iterable[DocumentRecord]) -> None:
        payload = [record.model_dump(mode="json") for record in records]
        self.settings.manifest_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def list_documents(self) -> list[DocumentRecord]:
        records = self._read()
        return sorted(records, key=lambda record: record.uploaded_at, reverse=True)

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        for record in self._read():
            if record.document_id == document_id:
                return record
        return None

    def upsert(self, record: DocumentRecord) -> None:
        records = self._read()
        filtered = [item for item in records if item.document_id != record.document_id]
        filtered.append(record)
        self._write(filtered)

    def remove(self, document_id: str) -> Optional[DocumentRecord]:
        records = self._read()
        removed: Optional[DocumentRecord] = None
        kept: list[DocumentRecord] = []
        for record in records:
            if record.document_id == document_id:
                removed = record
                continue
            kept.append(record)
        self._write(kept)
        return removed
