"""Relationship graph generation and analysis."""

from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
import json

from nyx.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Node:
    """Graph node."""

    id: str
    label: str
    node_type: str
    attributes: Dict[str, Any]


@dataclass
class Edge:
    """Graph edge."""

    source: str
    target: str
    edge_type: str
    weight: float
    attributes: Dict[str, Any]


class RelationshipGraph:
    """Build and analyze relationship graphs."""

    def __init__(self) -> None:
        """Initialize relationship graph."""
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def add_node(
        self, node_id: str, label: str, node_type: str, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add node to graph.

        Args:
            node_id: Node ID
            label: Node label
            node_type: Node type
            attributes: Node attributes
        """
        self.nodes[node_id] = Node(
            id=node_id, label=label, node_type=node_type, attributes=attributes or {}
        )

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        weight: float = 1.0,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add edge to graph.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Edge type
            weight: Edge weight
            attributes: Edge attributes
        """
        self.edges.append(
            Edge(
                source=source,
                target=target,
                edge_type=edge_type,
                weight=weight,
                attributes=attributes or {},
            )
        )

    def build_from_profiles(self, profiles: List[Dict[str, Any]]) -> None:
        """Build graph from profile data.

        Args:
            profiles: List of profile data
        """
        for profile in profiles:
            profile_id = profile.get("id", "")
            username = profile.get("username", "")
            platform = profile.get("platform", "")

            self.add_node(
                profile_id,
                f"{username}@{platform}",
                "profile",
                {"username": username, "platform": platform},
            )

            if profile.get("email"):
                email_id = f"email_{profile['email']}"
                self.add_node(email_id, profile["email"], "email", {"value": profile["email"]})
                self.add_edge(profile_id, email_id, "has_email")

            if profile.get("phone"):
                phone_id = f"phone_{profile['phone']}"
                self.add_node(phone_id, profile["phone"], "phone", {"value": profile["phone"]})
                self.add_edge(profile_id, phone_id, "has_phone")

            if profile.get("location"):
                location_id = f"location_{profile['location']}"
                self.add_node(
                    location_id, profile["location"], "location", {"value": profile["location"]}
                )
                self.add_edge(profile_id, location_id, "located_in")

        self._find_connections()

    def _find_connections(self) -> None:
        """Find connections between nodes based on shared attributes."""
        profiles = [n for n in self.nodes.values() if n.node_type == "profile"]

        for i, profile1 in enumerate(profiles):
            for profile2 in profiles[i + 1 :]:
                shared_attrs = self._find_shared_attributes(
                    profile1.attributes, profile2.attributes
                )

                if shared_attrs:
                    self.add_edge(
                        profile1.id,
                        profile2.id,
                        "related_to",
                        weight=len(shared_attrs) * 0.3,
                        attributes={"shared": shared_attrs},
                    )

    def _find_shared_attributes(
        self, attrs1: Dict[str, Any], attrs2: Dict[str, Any]
    ) -> List[str]:
        """Find shared attributes between two nodes."""
        shared = []
        for key in set(attrs1.keys()).intersection(set(attrs2.keys())):
            if attrs1[key] == attrs2[key] and attrs1[key]:
                shared.append(key)
        return shared

    def get_neighbors(self, node_id: str) -> List[Node]:
        """Get neighboring nodes.

        Args:
            node_id: Node ID

        Returns:
            List of neighboring nodes
        """
        neighbors = []
        neighbor_ids = set()

        for edge in self.edges:
            if edge.source == node_id:
                neighbor_ids.add(edge.target)
            elif edge.target == node_id:
                neighbor_ids.add(edge.source)

        for nid in neighbor_ids:
            if nid in self.nodes:
                neighbors.append(self.nodes[nid])

        return neighbors

    def get_connected_component(self, node_id: str) -> Set[str]:
        """Get connected component containing node.

        Args:
            node_id: Starting node ID

        Returns:
            Set of connected node IDs
        """
        if node_id not in self.nodes:
            return set()

        visited = set()
        queue = [node_id]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            neighbors = self.get_neighbors(current)

            for neighbor in neighbors:
                if neighbor.id not in visited:
                    queue.append(neighbor.id)

        return visited

    def calculate_centrality(self) -> Dict[str, float]:
        """Calculate degree centrality for all nodes.

        Returns:
            Dictionary of node ID to centrality score
        """
        centrality = {}

        for node_id in self.nodes:
            degree = len(self.get_neighbors(node_id))
            centrality[node_id] = degree

        max_degree = max(centrality.values()) if centrality else 1
        normalized = {k: v / max_degree for k, v in centrality.items()}

        return normalized

    def find_clusters(self) -> List[Set[str]]:
        """Find clusters in graph.

        Returns:
            List of clusters (sets of node IDs)
        """
        clusters = []
        visited = set()

        for node_id in self.nodes:
            if node_id not in visited:
                component = self.get_connected_component(node_id)
                clusters.append(component)
                visited.update(component)

        return clusters

    def export_json(self) -> str:
        """Export graph as JSON.

        Returns:
            JSON string
        """
        data = {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.node_type,
                    "attributes": n.attributes,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "type": e.edge_type,
                    "weight": e.weight,
                    "attributes": e.attributes,
                }
                for e in self.edges
            ],
        }

        return json.dumps(data, indent=2)

    def export_graphviz(self) -> str:
        """Export graph in Graphviz DOT format.

        Returns:
            DOT format string
        """
        lines = ["digraph G {"]
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box];')

        for node in self.nodes.values():
            color = {
                "profile": "lightblue",
                "email": "lightgreen",
                "phone": "lightyellow",
                "location": "lightpink",
            }.get(node.node_type, "white")

            lines.append(f'  "{node.id}" [label="{node.label}" fillcolor="{color}" style=filled];')

        for edge in self.edges:
            label = f"{edge.edge_type} ({edge.weight:.2f})"
            lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{label}"];')

        lines.append("}")
        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "node_types": {
                node_type: sum(1 for n in self.nodes.values() if n.node_type == node_type)
                for node_type in set(n.node_type for n in self.nodes.values())
            },
            "average_degree": sum(len(self.get_neighbors(n)) for n in self.nodes) / len(self.nodes)
            if self.nodes
            else 0,
            "clusters": len(self.find_clusters()),
        }
