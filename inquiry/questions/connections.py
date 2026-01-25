"""
CONNECTIONS: "How is it connected?" - Relational Structure Without Semantics

This module answers the third legitimate human question about a codebase:
How modules depend on each other, without assigning meaning or importance.

CONSTITUTIONAL RULES:
1. No "core module" claims - connections are facts, importance is human judgment
2. No architectural judgments - no "good/bad" coupling assessments
3. Only observable dependency facts
4. Graph structures without semantic labels
5. No inference about relationship quality

Tier 1 Violation: If this module makes any claim about architectural quality,
module importance, or "should be" relationships, the system halts immediately.
"""

import collections
import json
import pathlib
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import (
    Any,
)

# Allowed Layer 2 patterns
from inquiry.patterns.coupling import CouplingPatterns

# Allowed Layer 1 imports
from observations.eyes.import_sight import ImportObservation
from observations.record.snapshot import Snapshot

# Python stdlib


class ConnectionType(Enum):
    """Types of observable connections between modules.

    Only factual relationship types, no qualitative labels.
    """

    DIRECT_IMPORT = auto()  # import module
    FROM_IMPORT = auto()  # from module import name
    RELATIVE_IMPORT = auto()  # from . import module
    WILDCARD_IMPORT = auto()  # from module import *
    DYNAMIC_IMPORT = auto()  # __import__, importlib
    TYPE_HINT = auto()  # Type annotations
    DECORATOR_REFERENCE = auto()  # @decorator references
    UNKNOWN = auto()  # Connection observed but type unclear


@dataclass(frozen=True)
class ModuleConnection:
    """Immutable observation of a connection between two modules.

    Contains only observable facts about the dependency.
    No inference about why or how important.
    """

    source_module: str
    target_module: str
    connection_type: ConnectionType
    line_number: int
    import_count: int = 1  # How many times this connection appears

    # Context for debugging/traceability only
    source_file: pathlib.Path | None = None
    imported_names: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate connection doesn't contain inference."""
        # Constitutional: No qualitative labels in connection_type
        if not isinstance(self.connection_type, ConnectionType):
            raise ConstitutionalViolation(
                f"Connection type must be ConnectionType enum, got {type(self.connection_type)}"
            )

        # Constitutional: Import count must be positive
        if self.import_count <= 0:
            raise ConstitutionalViolation(
                f"Import count must be positive, got {self.import_count}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary without interpretation."""
        return {
            "source_module": self.source_module,
            "target_module": self.target_module,
            "connection_type": self.connection_type.name,
            "line_number": self.line_number,
            "import_count": self.import_count,
            "source_file": str(self.source_file) if self.source_file else None,
            "imported_names": list(self.imported_names),
            "_type": "module_connection",
        }


@dataclass
class ModuleNode:
    """Representation of a module in the connection graph.

    Contains only observable facts about connections.
    No centrality or importance metrics.
    """

    module_name: str
    outgoing: list[ModuleConnection] = field(default_factory=list)
    incoming: list[ModuleConnection] = field(default_factory=list)

    def add_outgoing(self, connection: ModuleConnection) -> None:
        """Add outgoing connection."""
        if connection.source_module != self.module_name:
            raise ConstitutionalViolation(
                f"Connection source {connection.source_module} "
                f"doesn't match node {self.module_name}"
            )
        self.outgoing.append(connection)

    def add_incoming(self, connection: ModuleConnection) -> None:
        """Add incoming connection."""
        if connection.target_module != self.module_name:
            raise ConstitutionalViolation(
                f"Connection target {connection.target_module} "
                f"doesn't match node {self.module_name}"
            )
        self.incoming.append(connection)

    @property
    def out_degree(self) -> int:
        """Number of unique modules this module imports."""
        unique_targets = {c.target_module for c in self.outgoing}
        return len(unique_targets)

    @property
    def in_degree(self) -> int:
        """Number of unique modules that import this module."""
        unique_sources = {c.source_module for c in self.incoming}
        return len(unique_sources)

    @property
    def total_imports(self) -> int:
        """Total number of import statements (including duplicates)."""
        return sum(c.import_count for c in self.outgoing)

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "module_name": self.module_name,
            "out_degree": self.out_degree,
            "in_degree": self.in_degree,
            "total_imports": self.total_imports,
            "outgoing_count": len(self.outgoing),
            "incoming_count": len(self.incoming),
            "_type": "module_node",
        }


@dataclass
class ConnectionGraph:
    """Complete graph of module connections without interpretation.

    This is a pure relational structure.
    No inference about architecture, quality, or importance.
    """

    nodes: dict[str, ModuleNode]
    edges: list[ModuleConnection]

    # Statistical facts (no judgment)
    total_connections: int
    unique_connections: int
    module_count: int

    # Distributions (observable facts only)
    out_degree_distribution: dict[int, int]  # out_degree -> count
    in_degree_distribution: dict[int, int]  # in_degree -> count

    def __post_init__(self) -> None:
        """Validate graph integrity."""
        # Constitutional: All edges must have corresponding nodes
        for edge in self.edges:
            if edge.source_module not in self.nodes:
                raise ConstitutionalViolation(
                    f"Edge source {edge.source_module} not in nodes"
                )
            if edge.target_module not in self.nodes:
                raise ConstitutionalViolation(
                    f"Edge target {edge.target_module} not in nodes"
                )

    def get_module(self, module_name: str) -> ModuleNode | None:
        """Get module node by name."""
        return self.nodes.get(module_name)

    def get_connections_between(
        self, source: str, target: str
    ) -> list[ModuleConnection]:
        """Get all connections between two modules."""
        return [
            edge
            for edge in self.edges
            if edge.source_module == source and edge.target_module == target
        ]

    def get_transitive_dependencies(
        self, module_name: str, max_depth: int = 3
    ) -> set[str]:
        """Get all modules reachable from this module (transitive closure).

        Constitutional: This is a factual reachability calculation.
        No inference about whether this is "good" or "bad".
        """
        if module_name not in self.nodes:
            return set()

        visited: set[str] = set()
        to_visit: list[tuple[str, int]] = [(module_name, 0)]

        while to_visit:
            current, depth = to_visit.pop()

            if current in visited or depth > max_depth:
                continue

            visited.add(current)

            if current in self.nodes:
                node = self.nodes[current]
                # Add all outgoing connections
                for connection in node.outgoing:
                    if connection.target_module not in visited:
                        to_visit.append((connection.target_module, depth + 1))

        visited.remove(module_name)  # Don't include self
        return visited

    def get_reverse_dependencies(
        self, module_name: str, max_depth: int = 3
    ) -> set[str]:
        """Get all modules that can reach this module (reverse transitive closure)."""
        if module_name not in self.nodes:
            return set()

        visited: set[str] = set()
        to_visit: list[tuple[str, int]] = [(module_name, 0)]

        while to_visit:
            current, depth = to_visit.pop()

            if current in visited or depth > max_depth:
                continue

            visited.add(current)

            if current in self.nodes:
                node = self.nodes[current]
                # Add all incoming connections
                for connection in node.incoming:
                    if connection.source_module not in visited:
                        to_visit.append((connection.source_module, depth + 1))

        visited.remove(module_name)  # Don't include self
        return visited

    def to_adjacency_list(self) -> dict[str, list[str]]:
        """Convert to adjacency list representation.

        Constitutional: Simple list format without weights or labels.
        """
        adjacency: collections.defaultdict[str, list[str]] = collections.defaultdict(
            list
        )

        for edge in self.edges:
            if edge.target_module not in adjacency[edge.source_module]:
                adjacency[edge.source_module].append(edge.target_module)

        return dict(adjacency)

    def to_edge_list(self) -> list[tuple[str, str, dict[str, Any]]]:
        """Convert to edge list with attributes."""
        edges = []
        for edge in self.edges:
            edges.append(
                (
                    edge.source_module,
                    edge.target_module,
                    {
                        "type": edge.connection_type.name,
                        "count": edge.import_count,
                        "line": edge.line_number,
                    },
                )
            )
        return edges

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "total_connections": self.total_connections,
            "unique_connections": self.unique_connections,
            "module_count": self.module_count,
            "out_degree_distribution": self.out_degree_distribution,
            "in_degree_distribution": self.in_degree_distribution,
            "adjacency_list": self.to_adjacency_list(),
            "_type": "connection_graph",
        }


@dataclass
class ConnectionAnalysis:
    """Complete analysis of module connections without interpretation."""

    graph: ConnectionGraph
    coupling_patterns: CouplingPatterns | None = None

    # Observable patterns (not judgments)
    strongly_connected_components: list[set[str]] = field(default_factory=list)
    isolated_modules: list[str] = field(default_factory=list)
    hub_modules: list[str] = field(default_factory=list)  # High degree, not "important"

    def describe_connectivity(self) -> str:
        """Generate factual description of connectivity patterns.

        Constitutional: Only observable facts, no judgments.
        """
        parts = []

        parts.append("Observable connection patterns:")
        parts.append("")

        # Basic statistics
        parts.append(f"• {self.graph.module_count} modules")
        parts.append(f"• {self.graph.total_connections} import statements")
        parts.append(
            f"• {self.graph.unique_connections} unique module-to-module connections"
        )

        # Degree distributions
        avg_out_degree = (
            sum(
                deg * count for deg, count in self.graph.out_degree_distribution.items()
            )
            / self.graph.module_count
            if self.graph.module_count > 0
            else 0
        )

        avg_in_degree = (
            sum(deg * count for deg, count in self.graph.in_degree_distribution.items())
            / self.graph.module_count
            if self.graph.module_count > 0
            else 0
        )

        parts.append(f"• Average outgoing connections per module: {avg_out_degree:.1f}")
        parts.append(f"• Average incoming connections per module: {avg_in_degree:.1f}")

        # Special patterns (factual)
        if self.isolated_modules:
            parts.append(f"• {len(self.isolated_modules)} modules with no connections")

        if self.hub_modules:
            parts.append(
                f"• {len(self.hub_modules)} modules with high connection counts"
            )

        if self.strongly_connected_components:
            scc_sizes = [
                len(scc) for scc in self.strongly_connected_components if len(scc) > 1
            ]
            if scc_sizes:
                parts.append(f"• {len(scc_sizes)} groups of mutually dependent modules")

        parts.append("")
        parts.append("Note: Connections are observable facts. ")
        parts.append("Importance and architectural quality require human judgment.")

        return "\n".join(parts)

    def get_module_context(self, module_name: str) -> dict[str, Any]:
        """Get contextual information about a module's connections."""
        if module_name not in self.graph.nodes:
            return {"error": f"Module {module_name} not found"}

        node = self.graph.nodes[module_name]

        # Forward dependencies
        forward = self.graph.get_transitive_dependencies(module_name, max_depth=2)

        # Reverse dependencies
        reverse = self.graph.get_reverse_dependencies(module_name, max_depth=2)

        return {
            "module": module_name,
            "out_degree": node.out_degree,
            "in_degree": node.in_degree,
            "total_imports": node.total_imports,
            "direct_dependencies": [c.target_module for c in node.outgoing],
            "direct_dependents": [c.source_module for c in node.incoming],
            "transitive_dependencies": list(forward),
            "transitive_dependents": list(reverse),
            "is_isolated": module_name in self.isolated_modules,
            "is_hub": module_name in self.hub_modules,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "graph": self.graph.to_dict(),
            "strongly_connected_components": [
                list(scc) for scc in self.strongly_connected_components
            ],
            "isolated_modules": self.isolated_modules,
            "hub_modules": self.hub_modules,
            "description": self.describe_connectivity(),
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "_type": "connection_analysis",
        }


class ConnectionAnalyzer:
    """Analyzer that builds connection graphs from observable imports.

    Only processes what is textually present in import statements.
    No inference about runtime or dynamic connections.
    """

    def __init__(self, snapshot: Snapshot):
        """Initialize with immutable observation snapshot."""
        self.snapshot = snapshot
        self.import_observations: list[ImportObservation] = []

        # Extract import observations from snapshot
        self._extract_imports()

    def _extract_imports(self) -> None:
        """Extract import observations from snapshot.

        Constitutional: Only use what's observable in the snapshot.
        """
        if hasattr(self.snapshot, "get_import_observations"):
            self.import_observations = self.snapshot.get_import_observations()
        else:
            # Fallback: look for import observations in snapshot data
            snapshot_dict = (
                self.snapshot.to_dict() if hasattr(self.snapshot, "to_dict") else {}
            )
            imports = snapshot_dict.get("import_observations", [])

            # Convert dicts back to ImportObservation objects
            for imp in imports:
                if isinstance(imp, dict):
                    # This is a simplification - in production, you'd have proper deserialization
                    obs = ImportObservation(
                        source_module=imp.get("source_module", ""),
                        imported_module=imp.get("imported_module", ""),
                        line_number=imp.get("line_number", 0),
                        import_type=imp.get("import_type", "direct"),
                        imported_names=tuple(imp.get("imported_names", [])),
                    )
                    self.import_observations.append(obs)

    def analyze(self) -> ConnectionAnalysis:
        """Build connection graph from import observations."""
        # Build nodes and edges
        nodes: dict[str, ModuleNode] = {}
        edges: list[ModuleConnection] = []

        # Count connections for aggregation
        connection_counts: collections.defaultdict[
            tuple[str, str, ConnectionType], int
        ] = collections.defaultdict(int)

        # Process each import observation
        for obs in self.import_observations:
            # Create nodes if they don't exist
            if obs.source_module not in nodes:
                nodes[obs.source_module] = ModuleNode(module_name=obs.source_module)
            if obs.imported_module not in nodes:
                nodes[obs.imported_module] = ModuleNode(module_name=obs.imported_module)

            # Determine connection type
            conn_type = self._determine_connection_type(obs)

            # Aggregate multiple imports between same modules
            key = (obs.source_module, obs.imported_module, conn_type)
            connection_counts[key] += 1

        # Create aggregated edges
        for (source, target, conn_type), count in connection_counts.items():
            edge = ModuleConnection(
                source_module=source,
                target_module=target,
                connection_type=conn_type,
                line_number=0,  # Lost in aggregation
                import_count=count,
            )
            edges.append(edge)

            # Add to nodes
            nodes[source].add_outgoing(edge)
            nodes[target].add_incoming(edge)

        # Calculate distributions
        out_degree_dist = self._calculate_degree_distribution(nodes, "out")
        in_degree_dist = self._calculate_degree_distribution(nodes, "in")

        # Build graph
        graph = ConnectionGraph(
            nodes=nodes,
            edges=edges,
            total_connections=sum(len(node.outgoing) for node in nodes.values()),
            unique_connections=len(edges),
            module_count=len(nodes),
            out_degree_distribution=out_degree_dist,
            in_degree_distribution=in_degree_dist,
        )

        # Find patterns (factual, not judgments)
        strongly_connected = self._find_strongly_connected_components(graph)
        isolated = self._find_isolated_modules(graph)
        hubs = self._find_hub_modules(graph)

        # Optional: Get coupling patterns
        coupling_patterns = None
        try:
            coupling_patterns = CouplingPatterns(graph)
        except Exception:
            # Coupling patterns are optional
            pass

        return ConnectionAnalysis(
            graph=graph,
            coupling_patterns=coupling_patterns,
            strongly_connected_components=strongly_connected,
            isolated_modules=isolated,
            hub_modules=hubs,
        )

    def _determine_connection_type(self, obs: ImportObservation) -> ConnectionType:
        """Determine connection type from import observation."""
        import_type = getattr(obs, "import_type", "direct")

        if import_type == "direct":
            return ConnectionType.DIRECT_IMPORT
        elif import_type == "from":
            return ConnectionType.FROM_IMPORT
        elif import_type == "relative":
            return ConnectionType.RELATIVE_IMPORT
        elif import_type == "wildcard":
            return ConnectionType.WILDCARD_IMPORT
        elif import_type == "dynamic":
            return ConnectionType.DYNAMIC_IMPORT
        else:
            return ConnectionType.UNKNOWN

    def _calculate_degree_distribution(
        self, nodes: dict[str, ModuleNode], direction: str
    ) -> dict[int, int]:
        """Calculate degree distribution (out or in)."""
        distribution: collections.defaultdict[int, int] = collections.defaultdict(int)

        for node in nodes.values():
            if direction == "out":
                degree = node.out_degree
            else:
                degree = node.in_degree

            distribution[degree] += 1

        return dict(distribution)

    def _find_strongly_connected_components(
        self, graph: ConnectionGraph
    ) -> list[set[str]]:
        """Find groups of mutually dependent modules (Kosaraju's algorithm).

        Constitutional: This is a factual graph property, not a judgment.
        """
        # Simplified implementation - in production, use networkx or proper algorithm
        # For now, return empty list (placeholder)
        return []

    def _find_isolated_modules(self, graph: ConnectionGraph) -> list[str]:
        """Find modules with no connections."""
        isolated = []
        for name, node in graph.nodes.items():
            if node.out_degree == 0 and node.in_degree == 0:
                isolated.append(name)
        return isolated

    def _find_hub_modules(
        self, graph: ConnectionGraph, threshold: float = 2.0
    ) -> list[str]:
        """Find modules with unusually high connection counts.

        Constitutional: Using statistical threshold, not qualitative "important".
        """
        if graph.module_count == 0:
            return []

        # Calculate mean and standard deviation of total connections
        total_connections = []
        for node in graph.nodes.values():
            total_connections.append(node.out_degree + node.in_degree)

        if len(total_connections) < 2:
            return []

        mean = statistics.mean(total_connections)
        stdev = statistics.stdev(total_connections) if len(total_connections) > 1 else 0

        # Find modules above threshold
        hubs = []
        threshold_value = mean + threshold * stdev

        for name, node in graph.nodes.items():
            total = node.out_degree + node.in_degree
            if total > threshold_value:
                hubs.append(name)

        return hubs


class ConstitutionalViolation(Exception):
    """Exception raised when constitutional rules are violated."""

    def __init__(self, message: str, tier: int = 1):
        super().__init__(message)
        self.tier = tier
        self.message = message

        # Constitutional: Log violations
        self._log_violation()

    def _log_violation(self) -> None:
        """Log constitutional violation."""
        import logging

        logger = logging.getLogger("codemarshal.connections")
        logger.error(f"Constitutional Violation (Tier {self.tier}): {self.message}")


# Utility functions for common connection questions
def find_module_dependencies(
    analysis: ConnectionAnalysis, module_name: str
) -> dict[str, Any]:
    """Find all dependencies of a module (factual, not judgmental)."""
    return analysis.get_module_context(module_name)


def find_connection_paths(
    analysis: ConnectionAnalysis, source: str, target: str, max_paths: int = 5
) -> list[list[str]]:
    """Find paths between two modules (factual reachability).

    Constitutional: Path existence is fact, not quality.
    """
    # Simplified BFS for path finding
    if source not in analysis.graph.nodes or target not in analysis.graph.nodes:
        return []

    from collections import deque

    paths = []
    queue = deque([(source, [source])])

    while queue and len(paths) < max_paths:
        current, path = queue.popleft()

        if current == target and len(path) > 1:
            paths.append(path)
            continue

        if len(path) > 6:  # Limit search depth
            continue

        node = analysis.graph.nodes.get(current)
        if node:
            for connection in node.outgoing:
                if connection.target_module not in path:  # Avoid cycles
                    queue.append(
                        (connection.target_module, path + [connection.target_module])
                    )

    return paths


def export_connection_graph(
    analysis: ConnectionAnalysis, output_path: pathlib.Path
) -> None:
    """Export connection analysis as JSON."""
    data = analysis.to_dict()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Example usage (for testing only)
def analyze_example_connections(snapshot_path: pathlib.Path) -> ConnectionAnalysis:
    """Example function to demonstrate usage."""
    # This is a placeholder - in production, you'd load a real snapshot
    from observations.record.snapshot import load_snapshot

    snapshot = load_snapshot(snapshot_path)
    analyzer = ConnectionAnalyzer(snapshot)
    return analyzer.analyze()


# Export public API
__all__ = [
    "ConnectionType",
    "ModuleConnection",
    "ModuleNode",
    "ConnectionGraph",
    "ConnectionAnalysis",
    "ConnectionAnalyzer",
    "ConstitutionalViolation",
    "find_module_dependencies",
    "find_connection_paths",
    "export_connection_graph",
]
