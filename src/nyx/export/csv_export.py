"""CSV export functionality."""

import csv
from typing import Dict, Any, List, Optional
from pathlib import Path

from nyx.core.logger import get_logger

logger = get_logger(__name__)


class CSVExporter:
    """Export OSINT data to CSV format."""

    def __init__(self, delimiter: str = ",", quoting: int = csv.QUOTE_MINIMAL) -> None:
        """Initialize CSV exporter.

        Args:
            delimiter: Field delimiter
            quoting: Quoting style
        """
        self.delimiter = delimiter
        self.quoting = quoting

    def export(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        fieldnames: Optional[List[str]] = None,
        redact_fields: Optional[List[str]] = None,
    ) -> None:
        """Export data to CSV.

        Args:
            data: List of dictionaries to export
            output_path: Output file path
            fieldnames: Field names (order of columns)
            redact_fields: Fields to redact
        """
        try:
            if not data:
                logger.warning("No data to export")
                return

            if redact_fields:
                data = self._redact_fields(data, redact_fields)

            if not fieldnames:
                fieldnames = list(data[0].keys())

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=fieldnames, delimiter=self.delimiter, quoting=self.quoting
                )

                writer.writeheader()
                for row in data:
                    filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                    writer.writerow(filtered_row)

            logger.info(f"Exported CSV to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise

    def export_profiles(
        self,
        profiles: List[Dict[str, Any]],
        output_path: str,
        redact_fields: Optional[List[str]] = None,
    ) -> None:
        """Export profiles to CSV with flattened structure.

        Args:
            profiles: List of profiles
            output_path: Output file path
            redact_fields: Fields to redact
        """
        try:
            if not profiles:
                logger.warning("No profiles to export")
                return

            flattened = []
            all_keys = set()

            for profile in profiles:
                flat = self._flatten_dict(profile)
                flattened.append(flat)
                all_keys.update(flat.keys())

            fieldnames = sorted(all_keys)

            self.export(flattened, output_path, fieldnames=fieldnames, redact_fields=redact_fields)

        except Exception as e:
            logger.error(f"Failed to export profiles CSV: {e}")
            raise

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """Flatten nested dictionary.

        Args:
            d: Dictionary to flatten
            parent_key: Parent key for recursion
            sep: Separator for nested keys

        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, ", ".join(str(x) for x in v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def _redact_fields(self, data: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
        """Redact specified fields.

        Args:
            data: Data to redact
            fields: Fields to redact

        Returns:
            Redacted data
        """
        import copy

        redacted = copy.deepcopy(data)

        for item in redacted:
            for field in fields:
                if field in item:
                    item[field] = "[REDACTED]"

        return redacted
