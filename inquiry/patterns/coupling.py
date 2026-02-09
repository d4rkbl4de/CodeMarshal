"""
Graph topology measurement for CodeMarshal.

This module calculates degree, fan-in, fan-out, and adjacency in the import graph.
Coupling is geometry, not diagnosis. A hub is not a crime. A spoke is not virtue.
"""

import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

# Import from observations layer (allowed per architecture)
from observations.eyes.import_sight import ImportSight
from observations.record.snapshot import CodeSnapshot


class EdgeDirection(Enum):
    """Direction of import relationship."""

    INCOMING = auto()  # Module is imported by others
    OUTGOING = auto()  # Module imports others
    BIDIRECTIONAL = auto()  # Mutual import between two modules


@dataclass(frozen=True)
class NodeDegree:
    """Degree measurements for a single module node.

    Contains only numeric counts of relationships.
    No labels, no interpretations.
    """

    module_name: str
    fan_in: int  # Number of modules that import this module
    fan_out: int  # Number of modules this module imports
    total_degree: int  # fan_in + fan_out (undirected connections)

    @property
    def degree_balance(self) -> float:
        """Balance between incoming and outgoing edges.
        Positive = more incoming, Negative = more outgoing, 0 = balanced.
        """
        return float(self.fan_in - self.fan_out)

    @property
    def dependency_ratio(self) -> float:
        """Ratio of outgoing to total degree.
        0 = pure sink, 1 = pure source, 0.5 = balanced.
        """
        if self.total_degree == 0:
            return 0.0
        return self.fan_out / self.total_degree


@dataclass(frozen=True)
class GraphEdge:
    """Single directed edge in the import graph."""

    source_module: str
    target_module: str
    count: int  # Number of times this edge appears (if multiple imports)
    is_bidirectional: bool  # Whether reverse edge also exists

    @property
    def is_self_edge(self) -> bool:
        """Whether this is a self-reference."""
        return self.source_module == self.target_module


@dataclass(frozen=True)
class BidirectionalPair:
    """Pair of modules that import each other."""

    module_a: str
    module_b: str
    a_to_b_count: int  # Times A imports B
    b_to_a_count: int  # Times B imports A
    total_interactions: int  # a_to_b_count + b_to_a_count

    @property
    def symmetry_ratio(self) -> float:
        """How symmetric the relationship is.
        0.5 = perfectly symmetric, away from 0.5 = asymmetric.
        """
        if self.total_interactions == 0:
            return 0.5
        return min(self.a_to_b_count, self.b_to_a_count) / self.total_interactions


@dataclass(frozen=True)
class GraphTopology:
    """Complete topological measurements of the import graph.

    Contains only structural and numeric properties.
    No interpretations, no architectural roles.
    """

    node_count: int
    edge_count: int
    bidirectional_edge_count: int
    self_reference_count: int

    # Degree distributions
    max_fan_in: int
    max_fan_out: int
    avg_fan_in: float
    avg_fan_out: float
    avg_total_degree: float

    # Graph density
    density: float  # Actual edges / possible edges (0 to 1)

    # Clustering metrics
    average_clustering: float  # How connected neighbors are (0 to 1)

    @property
    def possible_edges(self) -> int:
        """Maximum possible edges in a directed graph (excluding self-edges)."""
        n = self.node_count
        return n * (n - 1) if n > 1 else 0


class CouplingCalculator:
    """Calculates graph topology metrics from import observations.

    This class:
    - Builds directed graph from import relationships
    - Computes fan-in, fan-out, bidirectional edges
    - Exposes raw degree counts and directional asymmetry

    It never:
    - Declares "tight coupling"
    - Recommends refactors
    - Infers architectural roles
    """

    def __init__(self, import_sight: ImportSight | None = None):
        """Initialize with optional import sight instance."""
        self._import_sight = import_sight or ImportSight()

    def build_directed_graph(
        self, snapshot: CodeSnapshot
    ) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
        """Build directed graph from import observations.

        Returns:
            Tuple of (outgoing_adjacency, incoming_adjacency)
            Each is dict mapping module -> set of connected modules
        """
        import_observations = self._import_sight.observe(snapshot)

        outgoing: dict[str, set[str]] = defaultdict(set)
        incoming: dict[str, set[str]] = defaultdict(set)

        for observation in import_observations:
            source = observation.source_module
            target = observation.imported_module

            outgoing[source].add(target)
            incoming[target].add(source)

        # Ensure all nodes appear in both dicts
        all_nodes = set(outgoing.keys()) | set(incoming.keys())
        for node in all_nodes:
            outgoing.setdefault(node, set())
            incoming.setdefault(node, set())

        return dict(outgoing), dict(incoming)

    def calculate_node_degrees(
        self,
        outgoing_adjacency: dict[str, set[str]],
        incoming_adjacency: dict[str, set[str]],
    ) -> tuple[NodeDegree, ...]:
        """Calculate degree metrics for each node.

        Returns:
            Tuple of NodeDegree objects, sorted by total_degree descending.
        """
        degrees: list[NodeDegree] = []

        # Get all nodes
        all_nodes = set(outgoing_adjacency.keys()) | set(incoming_adjacency.keys())

        for node in all_nodes:
            fan_out = len(outgoing_adjacency.get(node, set()))
            fan_in = len(incoming_adjacency.get(node, set()))
            total_degree = fan_in + fan_out

            degree = NodeDegree(
                module_name=node,
                fan_in=fan_in,
                fan_out=fan_out,
                total_degree=total_degree,
            )
            degrees.append(degree)

        # Sort by total degree for consistency
        degrees.sort(key=lambda d: d.total_degree, reverse=True)
        return tuple(degrees)

    def identify_edges(
        self, outgoing_adjacency: dict[str, set[str]]
    ) -> tuple[GraphEdge, ...]:
        """Identify all directed edges in the graph.

        Returns:
            Tuple of GraphEdge objects.
        """
        edges: list[GraphEdge] = []

        for source, targets in outgoing_adjacency.items():
            for target in targets:
                # Count occurrences (simple count for now)
                count = 1

                # Check if bidirectional
                is_bidirectional = (
                    target in outgoing_adjacency
                    and source in outgoing_adjacency[target]
                )

                edge = GraphEdge(
                    source_module=source,
                    target_module=target,
                    count=count,
                    is_bidirectional=is_bidirectional,
                )
                edges.append(edge)

        return tuple(edges)

    def identify_bidirectional_pairs(
        self, outgoing_adjacency: dict[str, set[str]]
    ) -> tuple[BidirectionalPair, ...]:
        """Identify all pairs of modules that import each other.

        Returns:
            Tuple of BidirectionalPair objects.
        """
        pairs: list[BidirectionalPair] = []
        processed: set[tuple[str, str]] = set()

        for node_a in outgoing_adjacency:
            for node_b in outgoing_adjacency.get(node_a, set()):
                # Check if we've already processed this pair
                pair_key = tuple(sorted([node_a, node_b]))
                if pair_key in processed:
                    continue

                # Check if bidirectional
                if (
                    node_b in outgoing_adjacency
                    and node_a in outgoing_adjacency[node_b]
                ):
                    # Count edges in both directions
                    a_to_b = 1 if node_b in outgoing_adjacency[node_a] else 0
                    b_to_a = 1 if node_a in outgoing_adjacency[node_b] else 0

                    pair = BidirectionalPair(
                        module_a=node_a,
                        module_b=node_b,
                        a_to_b_count=a_to_b,
                        b_to_a_count=b_to_a,
                        total_interactions=a_to_b + b_to_a,
                    )
                    pairs.append(pair)
                    processed.add(pair_key)

        return tuple(pairs)

    def calculate_graph_topology(
        self,
        node_degrees: Sequence[NodeDegree],
        edges: Sequence[GraphEdge],
        bidirectional_pairs: Sequence[BidirectionalPair],
    ) -> GraphTopology:
        """Calculate overall graph topology metrics.

        Returns:
            GraphTopology object with structural measurements.
        """
        if not node_degrees:
            return GraphTopology(
                node_count=0,
                edge_count=0,
                bidirectional_edge_count=0,
                self_reference_count=0,
                max_fan_in=0,
                max_fan_out=0,
                avg_fan_in=0.0,
                avg_fan_out=0.0,
                avg_total_degree=0.0,
                density=0.0,
                average_clustering=0.0,
            )

        # Counts
        node_count = len(node_degrees)
        edge_count = len(edges)

        bidirectional_edge_count = sum(1 for edge in edges if edge.is_bidirectional)

        self_reference_count = sum(1 for edge in edges if edge.is_self_edge)

        # Degree statistics
        max_fan_in = max(degree.fan_in for degree in node_degrees)
        max_fan_out = max(degree.fan_out for degree in node_degrees)
        avg_fan_in = sum(degree.fan_in for degree in node_degrees) / node_count
        avg_fan_out = sum(degree.fan_out for degree in node_degrees) / node_count
        avg_total_degree = (
            sum(degree.total_degree for degree in node_degrees) / node_count
        )

        # Graph density (directed, no self-loops)
        possible_edges = node_count * (node_count - 1) if node_count > 1 else 0
        if possible_edges > 0:
            # Count unique directed edges (excluding self-edges)
            unique_edges = len(
                {
                    (edge.source_module, edge.target_module)
                    for edge in edges
                    if not edge.is_self_edge
                }
            )
            density = unique_edges / possible_edges
        else:
            density = 0.0

        # Calculate average clustering coefficient (simplified)
        average_clustering = self._calculate_average_clustering(node_degrees)

        return GraphTopology(
            node_count=node_count,
            edge_count=edge_count,
            bidirectional_edge_count=bidirectional_edge_count,
            self_reference_count=self_reference_count,
            max_fan_in=max_fan_in,
            max_fan_out=max_fan_out,
            avg_fan_in=avg_fan_in,
            avg_fan_out=avg_fan_out,
            avg_total_degree=avg_total_degree,
            density=density,
            average_clustering=average_clustering,
        )

    def _calculate_average_clustering(
        self, node_degrees: Sequence[NodeDegree]
    ) -> float:
        """Calculate simplified average clustering coefficient.

        This is a proxy for how interconnected neighborhoods are.
        Returns value between 0 and 1.
        """
        if not node_degrees:
            return 0.0

        # Simple heuristic: proportion of nodes with both fan_in and fan_out > 0
        clustered_nodes = sum(
            1 for degree in node_degrees if degree.fan_in > 0 and degree.fan_out > 0
        )

        return clustered_nodes / len(node_degrees)

    def calculate_adjacency_matrix(
        self, outgoing_adjacency: dict[str, set[str]]
    ) -> tuple[list[str], list[list[int]]]:
        """Create adjacency matrix representation.

        Returns:
            Tuple of (node_labels, adjacency_matrix)
            adjacency_matrix[i][j] = 1 if node i -> node j, else 0
        """
        # Get all nodes in consistent order
        all_nodes = sorted(outgoing_adjacency.keys())
        node_index = {node: idx for idx, node in enumerate(all_nodes)}

        # Initialize matrix with zeros
        n = len(all_nodes)
        matrix = [[0] * n for _ in range(n)]

        # Fill matrix
        for source, targets in outgoing_adjacency.items():
            i = node_index[source]
            for target in targets:
                j = node_index.get(target)
                if j is not None:
                    matrix[i][j] = 1

        return all_nodes, matrix


def calculate_coupling_pattern(
    snapshot: CodeSnapshot, import_sight: ImportSight | None = None
) -> dict:
    """Main coupling calculation function for pattern registry.

    This is the function that will be registered in patterns/__init__.py.

    Returns:
        Dict with numeric coupling measurements only.
    """
    calculator = CouplingCalculator(import_sight)

    # Build graph
    outgoing_adjacency, incoming_adjacency = calculator.build_directed_graph(snapshot)

    # Calculate metrics
    node_degrees = calculator.calculate_node_degrees(
        outgoing_adjacency, incoming_adjacency
    )
    edges = calculator.identify_edges(outgoing_adjacency)
    bidirectional_pairs = calculator.identify_bidirectional_pairs(outgoing_adjacency)
    topology = calculator.calculate_graph_topology(
        node_degrees, edges, bidirectional_pairs
    )

    # Create adjacency matrix (optional, for structural analysis)
    node_labels, adjacency_matrix = calculator.calculate_adjacency_matrix(
        outgoing_adjacency
    )

    # Convert to serializable format
    result: dict = {
        "topology": {
            "node_count": topology.node_count,
            "edge_count": topology.edge_count,
            "bidirectional_edge_count": topology.bidirectional_edge_count,
            "self_reference_count": topology.self_reference_count,
            "max_fan_in": topology.max_fan_in,
            "max_fan_out": topology.max_fan_out,
            "avg_fan_in": topology.avg_fan_in,
            "avg_fan_out": topology.avg_fan_out,
            "avg_total_degree": topology.avg_total_degree,
            "density": topology.density,
            "average_clustering": topology.average_clustering,
            "possible_edges": topology.possible_edges,
        },
        "node_degrees": [],
        "edges": [],
        "bidirectional_pairs": [],
        "adjacency": {"node_labels": node_labels, "matrix": adjacency_matrix},
    }

    # Add node degrees (top 100 for performance)
    top_degrees = list(node_degrees)[:100]
    for degree in top_degrees:
        result["node_degrees"].append(
            {
                "module_name": degree.module_name,
                "fan_in": degree.fan_in,
                "fan_out": degree.fan_out,
                "total_degree": degree.total_degree,
                "degree_balance": degree.degree_balance,
                "dependency_ratio": degree.dependency_ratio,
            }
        )

    # Add edges (top 200 for performance)
    top_edges = list(edges)[:200]
    for edge in top_edges:
        result["edges"].append(
            {
                "source_module": edge.source_module,
                "target_module": edge.target_module,
                "count": edge.count,
                "is_bidirectional": edge.is_bidirectional,
                "is_self_edge": edge.is_self_edge,
            }
        )

    # Add bidirectional pairs (all of them, usually not many)
    for pair in bidirectional_pairs:
        result["bidirectional_pairs"].append(
            {
                "module_a": pair.module_a,
                "module_b": pair.module_b,
                "a_to_b_count": pair.a_to_b_count,
                "b_to_a_count": pair.b_to_a_count,
                "total_interactions": pair.total_interactions,
                "symmetry_ratio": pair.symmetry_ratio,
            }
        )

    # Calculate degree distributions
    if node_degrees:
        fan_in_values = [degree.fan_in for degree in node_degrees]
        fan_out_values = [degree.fan_out for degree in node_degrees]
        total_degree_values = [degree.total_degree for degree in node_degrees]

        result["degree_distributions"] = {
            "fan_in": _calculate_distribution_stats(fan_in_values),
            "fan_out": _calculate_distribution_stats(fan_out_values),
            "total_degree": _calculate_distribution_stats(total_degree_values),
        }

    # Calculate graph components
    components = _find_connected_components(outgoing_adjacency, incoming_adjacency)
    result["components"] = {
        "count": len(components),
        "sizes": [len(comp) for comp in components],
        "largest_component_size": max(len(comp) for comp in components)
        if components
        else 0,
    }

    return result


def _calculate_distribution_stats(values: list[int]) -> dict:
    """Calculate distribution statistics for a list of values."""
    if not values:
        return {}

    try:
        return {
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "q1": statistics.quantiles(values, n=4)[0] if len(values) >= 4 else 0,
            "q3": statistics.quantiles(values, n=4)[2] if len(values) >= 4 else 0,
        }
    except (statistics.StatisticsError, ValueError):
        return {}


def _find_connected_components(
    outgoing: dict[str, set[str]], incoming: dict[str, set[str]]
) -> list[list[str]]:
    """Find weakly connected components in the directed graph."""
    visited: set[str] = set()
    components: list[list[str]] = []

    all_nodes = set(outgoing.keys()) | set(incoming.keys())

    def dfs(node: str, component: list[str]):
        """Depth-first search for weak connectivity."""
        visited.add(node)
        component.append(node)

        # Check neighbors in both directions
        neighbors = outgoing.get(node, set()) | incoming.get(node, set())
        for neighbor in neighbors:
            if neighbor not in visited:
                dfs(neighbor, component)

    for node in all_nodes:
        if node not in visited:
            component: list[str] = []
            dfs(node, component)
            components.append(sorted(component))

    return sorted(components, key=len, reverse=True)


class CouplingPatterns:
    """Lightweight wrapper for coupling metrics used by inquiry layer."""

    def __init__(self, graph: Any):
        self.graph = graph
        self.module_count = getattr(graph, "module_count", 0)
        if not self.module_count and hasattr(graph, "nodes"):
            self.module_count = len(getattr(graph, "nodes", {}))
        self.unique_connections = getattr(graph, "unique_connections", 0)
        if not self.unique_connections and hasattr(graph, "edges"):
            self.unique_connections = len(getattr(graph, "edges", []))
        self.total_connections = getattr(graph, "total_connections", 0)

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "module_count": self.module_count,
            "unique_connections": self.unique_connections,
            "total_connections": self.total_connections,
        }


def validate_coupling_output(data: dict) -> tuple[bool, list[str]]:
    """Validate that coupling output maintains invariants.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: list[str] = []

    # Check required structure
    required_sections = [
        "topology",
        "node_degrees",
        "edges",
        "bidirectional_pairs",
        "adjacency",
    ]
    for section in required_sections:
        if section not in data:
            errors.append(f"Missing required section: {section}")

    # Check topology for numeric values only
    topology = data.get("topology", {})
    topology_fields = [
        "node_count",
        "edge_count",
        "bidirectional_edge_count",
        "self_reference_count",
        "max_fan_in",
        "max_fan_out",
        "avg_fan_in",
        "avg_fan_out",
        "avg_total_degree",
        "density",
        "average_clustering",
    ]

    for field in topology_fields:
        value = topology.get(field)
        if value is not None and not isinstance(value, (int, float)):
            errors.append(f"Topology field {field} must be numeric")

    # Check density bounds
    density = topology.get("density", 0)
    if not isinstance(density, (int, float)):
        errors.append("Density must be numeric")
    elif density < 0 or density > 1:
        errors.append(f"Density out of bounds: {density}")

    # Check clustering bounds
    clustering = topology.get("average_clustering", 0)
    if not isinstance(clustering, (int, float)):
        errors.append("Average clustering must be numeric")
    elif clustering < 0 or clustering > 1:
        errors.append(f"Average clustering out of bounds: {clustering}")

    # Check for prohibited fields
    prose_fields = [
        "coupling",
        "tight",
        "loose",
        "cohesive",
        "problem",
        "warning",
        "recommendation",
        "should",
        "could",
    ]

    def check_for_prose(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_lower = str(key).lower()
                if any(prose in key_lower for prose in prose_fields):
                    errors.append(f"Prose-like field at {path}.{key}")
                check_for_prose(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_for_prose(item, f"{path}[{i}]")

    check_for_prose(data)

    # Check adjacency matrix consistency
    adjacency = data.get("adjacency", {})
    node_labels = adjacency.get("node_labels", [])
    matrix = adjacency.get("matrix", [])

    if node_labels and matrix:
        if len(matrix) != len(node_labels):
            errors.append("Adjacency matrix size doesn't match node labels")
        for row in matrix:
            if len(row) != len(node_labels):
                errors.append("Adjacency matrix row size doesn't match node labels")

    return (len(errors) == 0, errors)


# Test function to verify invariants
def test_coupling_invariants() -> tuple[bool, list[str]]:
    """Test that the module maintains its invariants.

    Returns:
        Tuple of (all_passed, list_of_failed_tests)
    """
    failures: list[str] = []

    try:
        from unittest.mock import Mock

        # Create a mock snapshot for testing
        mock_snapshot = Mock(spec=CodeSnapshot)

        # Test 1: Output contains only allowed data types
        result = calculate_coupling_pattern(mock_snapshot)

        # Check types
        if not isinstance(result, dict):
            failures.append("Result should be dict")

        topology = result.get("topology", {})
        if not isinstance(topology.get("density"), (int, float)):
            failures.append("Density must be numeric")

        # Test 2: No prose in outputs
        is_valid, errors = validate_coupling_output(result)
        if not is_valid:
            failures.extend(errors)

        # Test 3: All measurements are numeric or structural
        adjacency = result.get("adjacency", {})
        matrix = adjacency.get("matrix", [])
        if matrix:
            if not isinstance(matrix, list):
                failures.append("Adjacency matrix must be list")
            elif matrix and not all(isinstance(row, list) for row in matrix):
                failures.append("Adjacency matrix rows must be lists")
            elif (
                matrix
                and matrix[0]
                and not all(isinstance(val, int) for val in matrix[0])
            ):
                failures.append("Adjacency matrix values must be integers")

        # Test 4: Data structures are immutable
        CouplingCalculator()

        # Create test data
        test_degree = NodeDegree(
            module_name="test", fan_in=2, fan_out=3, total_degree=5
        )

        # Try to modify (should fail for frozen dataclass)
        try:
            test_degree.fan_in = 4  # type: ignore
            failures.append("NodeDegree should be immutable")
        except (AttributeError, dataclasses.FrozenInstanceError):
            pass  # Expected

        # Test 5: Deterministic outputs
        result1 = calculate_coupling_pattern(mock_snapshot)
        result2 = calculate_coupling_pattern(mock_snapshot)

        # Check that topology values are the same
        if result1.get("topology") != result2.get("topology"):
            failures.append("Topology measurements not deterministic")

        # Test 6: No interpretation in adjacency matrix
        # Adjacency matrix should only contain 0s and 1s, not weights or labels
        if "adjacency" in result1:
            matrix = result1["adjacency"].get("matrix", [])
            for row in matrix:
                for val in row:
                    if val not in [0, 1]:
                        failures.append(
                            f"Adjacency matrix contains non-binary value: {val}"
                        )

    except Exception as e:
        failures.append(f"Test failed with exception: {e}")

    return (len(failures) == 0, failures)


# Import at bottom to avoid circular imports
import dataclasses  # noqa: E402
from collections.abc import Sequence  # noqa: E402

if __name__ == "__main__":
    # Run invariant tests when executed directly
    passed, failures = test_coupling_invariants()

    if passed:
        print("✓ All coupling invariants maintained")
        print("  - Outputs are numeric/structural only")
        print("  - No prose or interpretation")
        print("  - No coupling judgments (tight/loose)")
        print("  - Data structures immutable")
        print("  - Adjacency matrix is binary")
    else:
        print("✗ Coupling invariant failures:")
        for failure in failures:
            print(f"  - {failure}")
        exit(1)
