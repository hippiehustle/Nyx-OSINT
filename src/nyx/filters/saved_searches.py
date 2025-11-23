"""Saved searches and search history management."""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from nyx.core.logger import get_logger
from nyx.filters.advanced import FilterRule, FilterOperator

logger = get_logger(__name__)


@dataclass
class SavedSearch:
    """Saved search definition."""

    id: str
    name: str
    description: str
    query: str
    filters: List[FilterRule]
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    metadata: Dict[str, Any]


class SavedSearchManager:
    """Manager for saved searches."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize saved search manager.

        Args:
            storage_path: Path to storage file
        """
        self.storage_path = Path(storage_path or "./data/saved_searches.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.searches: Dict[str, SavedSearch] = {}
        self._load()

    def _load(self) -> None:
        """Load saved searches from storage."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            for search_data in data:
                filters = []
                for filter_data in search_data.get("filters", []):
                    filters.append(
                        FilterRule(
                            field=filter_data["field"],
                            operator=FilterOperator(filter_data["operator"]),
                            value=filter_data["value"],
                            case_sensitive=filter_data.get("case_sensitive", False),
                        )
                    )

                search = SavedSearch(
                    id=search_data["id"],
                    name=search_data["name"],
                    description=search_data["description"],
                    query=search_data["query"],
                    filters=filters,
                    created_at=datetime.fromisoformat(search_data["created_at"]),
                    updated_at=datetime.fromisoformat(search_data["updated_at"]),
                    tags=search_data.get("tags", []),
                    metadata=search_data.get("metadata", {}),
                )
                self.searches[search.id] = search

            logger.info(f"Loaded {len(self.searches)} saved searches")
        except Exception as e:
            logger.error(f"Failed to load saved searches: {e}")

    def _save(self) -> None:
        """Save searches to storage."""
        try:
            data = []
            for search in self.searches.values():
                search_data = {
                    "id": search.id,
                    "name": search.name,
                    "description": search.description,
                    "query": search.query,
                    "filters": [
                        {
                            "field": f.field,
                            "operator": f.operator.value,
                            "value": f.value,
                            "case_sensitive": f.case_sensitive,
                        }
                        for f in search.filters
                    ],
                    "created_at": search.created_at.isoformat(),
                    "updated_at": search.updated_at.isoformat(),
                    "tags": search.tags,
                    "metadata": search.metadata,
                }
                data.append(search_data)

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.searches)} searches")
        except Exception as e:
            logger.error(f"Failed to save searches: {e}")

    def create(
        self,
        name: str,
        query: str,
        filters: List[FilterRule],
        description: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SavedSearch:
        """Create new saved search.

        Args:
            name: Search name
            query: Query string
            filters: Filter rules
            description: Search description
            tags: Tags for categorization
            metadata: Additional metadata

        Returns:
            Created saved search
        """
        import uuid

        search_id = str(uuid.uuid4())
        now = datetime.now()

        search = SavedSearch(
            id=search_id,
            name=name,
            description=description,
            query=query,
            filters=filters,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            metadata=metadata or {},
        )

        self.searches[search_id] = search
        self._save()

        logger.info(f"Created saved search: {name}")
        return search

    def update(
        self,
        search_id: str,
        name: Optional[str] = None,
        query: Optional[str] = None,
        filters: Optional[List[FilterRule]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SavedSearch]:
        """Update saved search.

        Args:
            search_id: Search ID
            name: New name
            query: New query
            filters: New filters
            description: New description
            tags: New tags
            metadata: New metadata

        Returns:
            Updated search or None
        """
        if search_id not in self.searches:
            return None

        search = self.searches[search_id]

        if name is not None:
            search.name = name
        if query is not None:
            search.query = query
        if filters is not None:
            search.filters = filters
        if description is not None:
            search.description = description
        if tags is not None:
            search.tags = tags
        if metadata is not None:
            search.metadata = metadata

        search.updated_at = datetime.now()
        self._save()

        logger.info(f"Updated saved search: {search.name}")
        return search

    def delete(self, search_id: str) -> bool:
        """Delete saved search.

        Args:
            search_id: Search ID

        Returns:
            True if deleted, False otherwise
        """
        if search_id in self.searches:
            del self.searches[search_id]
            self._save()
            logger.info(f"Deleted saved search: {search_id}")
            return True
        return False

    def get(self, search_id: str) -> Optional[SavedSearch]:
        """Get saved search by ID.

        Args:
            search_id: Search ID

        Returns:
            Saved search or None
        """
        return self.searches.get(search_id)

    def list_all(self) -> List[SavedSearch]:
        """List all saved searches.

        Returns:
            List of saved searches
        """
        return list(self.searches.values())

    def search_by_tag(self, tag: str) -> List[SavedSearch]:
        """Search saved searches by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching saved searches
        """
        return [s for s in self.searches.values() if tag in s.tags]

    def search_by_name(self, name: str) -> List[SavedSearch]:
        """Search saved searches by name.

        Args:
            name: Name to search for

        Returns:
            List of matching saved searches
        """
        name_lower = name.lower()
        return [s for s in self.searches.values() if name_lower in s.name.lower()]
