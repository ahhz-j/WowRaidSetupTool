from __future__ import annotations

import base64
import json
import zlib
from typing import Any


class ImportExportService:
    PROTOCOL_VERSION = 1

    def export_payload(self, payload_type: str, payload: dict[str, Any]) -> str:
        envelope = {
            "protocol_version": self.PROTOCOL_VERSION,
            "payload_type": payload_type,
            "payload": payload,
        }
        raw = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
        compressed = zlib.compress(raw)
        return base64.b64encode(compressed).decode("ascii")

    def import_payload(self, content: str) -> dict[str, Any]:
        compressed = base64.b64decode(content.encode("ascii"))
        raw = zlib.decompress(compressed)
        return json.loads(raw.decode("utf-8"))
