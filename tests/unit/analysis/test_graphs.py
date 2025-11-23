"""Tests for relationship graph module."""

import pytest
from nyx.analysis.graphs import RelationshipGraph


class TestRelationshipGraph:
    """Test relationship graph functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.graph = RelationshipGraph()

    def test_add_node(self):
        """Test adding nodes."""
        self.graph.add_node("1", "User1", "profile")
        assert "1" in self.graph.nodes
        assert self.graph.nodes["1"].label == "User1"

    def test_add_edge(self):
        """Test adding edges."""
        self.graph.add_node("1", "User1", "profile")
        self.graph.add_node("2", "User2", "profile")
        self.graph.add_edge("1", "2", "related_to")
        assert len(self.graph.edges) == 1

    def test_get_neighbors(self):
        """Test getting neighbors."""
        self.graph.add_node("1", "User1", "profile")
        self.graph.add_node("2", "User2", "profile")
        self.graph.add_node("3", "User3", "profile")
        self.graph.add_edge("1", "2", "related_to")
        self.graph.add_edge("1", "3", "related_to")

        neighbors = self.graph.get_neighbors("1")
        assert len(neighbors) == 2

    def test_get_connected_component(self):
        """Test getting connected component."""
        self.graph.add_node("1", "User1", "profile")
        self.graph.add_node("2", "User2", "profile")
        self.graph.add_node("3", "User3", "profile")
        self.graph.add_node("4", "User4", "profile")

        self.graph.add_edge("1", "2", "related_to")
        self.graph.add_edge("2", "3", "related_to")

        component = self.graph.get_connected_component("1")
        assert len(component) == 3
        assert "4" not in component

    def test_find_clusters(self):
        """Test finding clusters."""
        self.graph.add_node("1", "User1", "profile")
        self.graph.add_node("2", "User2", "profile")
        self.graph.add_node("3", "User3", "profile")
        self.graph.add_node("4", "User4", "profile")

        self.graph.add_edge("1", "2", "related_to")
        self.graph.add_edge("3", "4", "related_to")

        clusters = self.graph.find_clusters()
        assert len(clusters) == 2

    def test_export_json(self):
        """Test JSON export."""
        self.graph.add_node("1", "User1", "profile")
        self.graph.add_node("2", "User2", "profile")
        self.graph.add_edge("1", "2", "related_to")

        json_output = self.graph.export_json()
        assert "nodes" in json_output
        assert "edges" in json_output

    def test_get_statistics(self):
        """Test graph statistics."""
        self.graph.add_node("1", "User1", "profile")
        self.graph.add_node("2", "User2", "profile")
        self.graph.add_edge("1", "2", "related_to")

        stats = self.graph.get_statistics()
        assert stats["node_count"] == 2
        assert stats["edge_count"] == 1
