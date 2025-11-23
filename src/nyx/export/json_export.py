"""JSON export functionality."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from nyx.core.logger import get_logger

logger = get_logger(__name__)


class JSONExporter:
    """Export OSINT data to JSON format."""

    def __init__(self, pretty: bool = True) -> None:
        """Initialize JSON exporter.

        Args:
            pretty: Whether to use pretty printing
        """
        self.pretty = pretty

    def export(
        self,
        data: Dict[str, Any],
        output_path: str,
        include_metadata: bool = True,
        redact_fields: Optional[List[str]] = None,
    ) -> None:
        """Export data to JSON.

        Args:
            data: Data to export
            output_path: Output file path
            include_metadata: Whether to include metadata
            redact_fields: Fields to redact
        """
        try:
            if redact_fields:
                data = self._redact_fields(data, redact_fields)

            output_data = data.copy()

            if include_metadata:
                output_data["_metadata"] = {
                    "generated_at": datetime.now().isoformat(),
                    "generator": "Nyx OSINT Platform",
                    "version": "0.1.0",
                }

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                if self.pretty:
                    json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    json.dump(output_data, f, ensure_ascii=False, default=str)

            logger.info(f"Exported JSON to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise

    def export_compressed(
        self,
        data: Dict[str, Any],
        output_path: str,
        include_metadata: bool = True,
        redact_fields: Optional[List[str]] = None,
    ) -> None:
        """Export data to compressed JSON.

        Args:
            data: Data to export
            output_path: Output file path
            include_metadata: Whether to include metadata
            redact_fields: Fields to redact
        """
        import gzip

        try:
            if redact_fields:
                data = self._redact_fields(data, redact_fields)

            output_data = data.copy()

            if include_metadata:
                output_data["_metadata"] = {
                    "generated_at": datetime.now().isoformat(),
                    "generator": "Nyx OSINT Platform",
                    "version": "0.1.0",
                }

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            json_str = json.dumps(output_data, ensure_ascii=False, default=str)

            with gzip.open(output_path, "wt", encoding="utf-8") as f:
                f.write(json_str)

            logger.info(f"Exported compressed JSON to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export compressed JSON: {e}")
            raise

    def _redact_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Redact specified fields.

        Args:
            data: Data to redact
            fields: Fields to redact

        Returns:
            Redacted data
        """
        import copy

        redacted = copy.deepcopy(data)

        def redact_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                for key in list(obj.keys()):
                    if key in fields:
                        obj[key] = "[REDACTED]"
                    else:
                        obj[key] = redact_recursive(obj[key])
            elif isinstance(obj, list):
                return [redact_recursive(item) for item in obj]
            return obj

        return redact_recursive(redacted)
