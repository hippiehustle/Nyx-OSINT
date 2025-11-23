"""Timeline analysis for OSINT data."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from nyx.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TimelineEvent:
    """Timeline event."""

    id: str
    timestamp: datetime
    event_type: str
    source: str
    title: str
    description: str
    metadata: Dict[str, Any]


class TimelineAnalyzer:
    """Analyze temporal patterns in OSINT data."""

    def __init__(self) -> None:
        """Initialize timeline analyzer."""
        self.events: List[TimelineEvent] = []

    def add_event(
        self,
        event_id: str,
        timestamp: datetime,
        event_type: str,
        source: str,
        title: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add event to timeline.

        Args:
            event_id: Event ID
            timestamp: Event timestamp
            event_type: Event type
            source: Event source
            title: Event title
            description: Event description
            metadata: Event metadata
        """
        self.events.append(
            TimelineEvent(
                id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                source=source,
                title=title,
                description=description,
                metadata=metadata or {},
            )
        )

    def build_from_profiles(self, profiles: List[Dict[str, Any]]) -> None:
        """Build timeline from profile data.

        Args:
            profiles: List of profile data
        """
        for profile in profiles:
            if profile.get("created_at"):
                self.add_event(
                    f"profile_{profile.get('id')}",
                    profile["created_at"],
                    "profile_created",
                    profile.get("platform", ""),
                    f"Profile created: {profile.get('username', '')}",
                    metadata={"profile_id": profile.get("id"), "username": profile.get("username")},
                )

            if profile.get("last_activity"):
                self.add_event(
                    f"activity_{profile.get('id')}",
                    profile["last_activity"],
                    "last_activity",
                    profile.get("platform", ""),
                    f"Last activity: {profile.get('username', '')}",
                    metadata={"profile_id": profile.get("id"), "username": profile.get("username")},
                )

        self.events.sort(key=lambda e: e.timestamp)

    def get_events_in_range(
        self, start: datetime, end: datetime
    ) -> List[TimelineEvent]:
        """Get events in time range.

        Args:
            start: Start time
            end: End time

        Returns:
            List of events in range
        """
        return [e for e in self.events if start <= e.timestamp <= end]

    def get_events_by_type(self, event_type: str) -> List[TimelineEvent]:
        """Get events by type.

        Args:
            event_type: Event type

        Returns:
            List of matching events
        """
        return [e for e in self.events if e.event_type == event_type]

    def get_events_by_source(self, source: str) -> List[TimelineEvent]:
        """Get events by source.

        Args:
            source: Event source

        Returns:
            List of matching events
        """
        return [e for e in self.events if e.source == source]

    def find_temporal_patterns(self) -> List[Dict[str, Any]]:
        """Find temporal patterns in events.

        Returns:
            List of detected patterns
        """
        patterns = []

        activity_pattern = self._analyze_activity_pattern()
        if activity_pattern:
            patterns.append(activity_pattern)

        gaps = self._find_activity_gaps()
        if gaps:
            patterns.extend(gaps)

        clusters = self._find_temporal_clusters()
        if clusters:
            patterns.extend(clusters)

        return patterns

    def _analyze_activity_pattern(self) -> Optional[Dict[str, Any]]:
        """Analyze overall activity pattern."""
        if not self.events:
            return None

        timestamps = [e.timestamp for e in self.events]
        earliest = min(timestamps)
        latest = max(timestamps)
        span = (latest - earliest).days

        hourly_activity = [0] * 24
        for event in self.events:
            hourly_activity[event.timestamp.hour] += 1

        peak_hour = hourly_activity.index(max(hourly_activity))

        return {
            "pattern_type": "activity_pattern",
            "earliest_activity": earliest.isoformat(),
            "latest_activity": latest.isoformat(),
            "span_days": span,
            "total_events": len(self.events),
            "peak_hour": peak_hour,
            "description": f"Activity spans {span} days with peak at {peak_hour}:00",
        }

    def _find_activity_gaps(self, threshold_days: int = 30) -> List[Dict[str, Any]]:
        """Find gaps in activity."""
        if len(self.events) < 2:
            return []

        sorted_events = sorted(self.events, key=lambda e: e.timestamp)
        gaps = []

        for i in range(len(sorted_events) - 1):
            gap = (sorted_events[i + 1].timestamp - sorted_events[i].timestamp).days

            if gap >= threshold_days:
                gaps.append(
                    {
                        "pattern_type": "activity_gap",
                        "start": sorted_events[i].timestamp.isoformat(),
                        "end": sorted_events[i + 1].timestamp.isoformat(),
                        "gap_days": gap,
                        "description": f"{gap} day gap in activity",
                    }
                )

        return gaps

    def _find_temporal_clusters(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        """Find temporal clusters of activity."""
        if len(self.events) < 3:
            return []

        sorted_events = sorted(self.events, key=lambda e: e.timestamp)
        clusters = []
        current_cluster = [sorted_events[0]]

        for i in range(1, len(sorted_events)):
            time_diff = (sorted_events[i].timestamp - current_cluster[-1].timestamp).total_seconds() / 3600

            if time_diff <= window_hours:
                current_cluster.append(sorted_events[i])
            else:
                if len(current_cluster) >= 3:
                    clusters.append(
                        {
                            "pattern_type": "temporal_cluster",
                            "start": current_cluster[0].timestamp.isoformat(),
                            "end": current_cluster[-1].timestamp.isoformat(),
                            "event_count": len(current_cluster),
                            "description": f"Cluster of {len(current_cluster)} events",
                        }
                    )
                current_cluster = [sorted_events[i]]

        if len(current_cluster) >= 3:
            clusters.append(
                {
                    "pattern_type": "temporal_cluster",
                    "start": current_cluster[0].timestamp.isoformat(),
                    "end": current_cluster[-1].timestamp.isoformat(),
                    "event_count": len(current_cluster),
                    "description": f"Cluster of {len(current_cluster)} events",
                }
            )

        return clusters

    def export_json(self) -> str:
        """Export timeline as JSON.

        Returns:
            JSON string
        """
        data = {
            "events": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type,
                    "source": e.source,
                    "title": e.title,
                    "description": e.description,
                    "metadata": e.metadata,
                }
                for e in sorted(self.events, key=lambda x: x.timestamp)
            ]
        }

        return json.dumps(data, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get timeline statistics.

        Returns:
            Dictionary of statistics
        """
        if not self.events:
            return {
                "total_events": 0,
                "earliest": None,
                "latest": None,
                "span_days": 0,
                "event_types": {},
                "sources": {},
            }

        timestamps = [e.timestamp for e in self.events]
        earliest = min(timestamps)
        latest = max(timestamps)

        event_types = {}
        sources = {}

        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            sources[event.source] = sources.get(event.source, 0) + 1

        return {
            "total_events": len(self.events),
            "earliest": earliest.isoformat(),
            "latest": latest.isoformat(),
            "span_days": (latest - earliest).days,
            "event_types": event_types,
            "sources": sources,
        }
