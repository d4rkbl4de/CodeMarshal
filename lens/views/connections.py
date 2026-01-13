"""
Connections View - Declared Relationships Only (Truth Layer 3)

Core Responsibility: Display explicitly stated connections, not inferred ones.
This view shows what has been asserted, not what has been discovered.

Article 3: Truth Preservation - Never invent connections
Article 10: Anchored Thinking - All connections must have clear origin
Article 11: Declared Limitations - Show what connections cannot be seen
"""

from __future__ import annotations

import json
import textwrap
from typing import (
    Optional, List, Dict, Any, Set, FrozenSet, Tuple,
    Callable, ClassVar, Iterator, Union, cast, Literal
)
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict
from pathlib import Path

# Allowed imports per architecture
from lens.philosophy import (
    SingleFocusRule,
    ProgressiveDisclosureRule,
    ClarityRule,
    NavigationRule
)
from inquiry.session.context import SessionContext

# NOT ALLOWED: observations.*, patterns.*, bridge.commands.*


class ConnectionType(Enum):
    """Types of explicitly stated connections."""
    NOTE_ANCHOR = auto()          # Note anchored to observation
    OBSERVATION_REFERENCE = auto()  # Observation references another
    TEMPORAL_ADJACENCY = auto()   # Observations in temporal sequence
    STRUCTURAL_CONTAINMENT = auto()  # File in directory, etc.
    HUMAN_DECLARED = auto()       # Explicitly declared by human
    SOURCE_DECLARED = auto()      # Declared in source code (imports, calls)
    
    @property
    def display_name(self) -> str:
        """Human-readable name for connection type."""
        return {
            ConnectionType.NOTE_ANCHOR: "Note Anchor",
            ConnectionType.OBSERVATION_REFERENCE: "Observation Reference",
            ConnectionType.TEMPORAL_ADJACENCY: "Temporal Adjacency",
            ConnectionType.STRUCTURAL_CONTAINMENT: "Structural Containment",
            ConnectionType.HUMAN_DECLARED: "Human Declared",
            ConnectionType.SOURCE_DECLARED: "Source Declared"
        }[self]
    
    @property
    def icon(self) -> str:
        """Icon for connection type."""
        return {
            ConnectionType.NOTE_ANCHOR: "📌",
            ConnectionType.OBSERVATION_REFERENCE: "🔗",
            ConnectionType.TEMPORAL_ADJACENCY: "⏱️",
            ConnectionType.STRUCTURAL_CONTAINMENT: "📁",
            ConnectionType.HUMAN_DECLARED: "👤",
            ConnectionType.SOURCE_DECLARED: "📄"
        }[self]


class ConnectionStrength(Enum):
    """Strength of connection based on declaration."""
    EXPLICIT = auto()      # Direct, unambiguous statement
    INFERRED = auto()      # Not allowed in this view
    WEAK = auto()         # Indirect or uncertain
    UNKNOWN = auto()      # Strength not specified
    
    @property
    def display_symbol(self) -> str:
        """Visual indicator for strength."""
        return {
            ConnectionStrength.EXPLICIT: "✅",
            ConnectionStrength.INFERRED: "⚠️",  # Should never appear
            ConnectionStrength.WEAK: "🔄",
            ConnectionStrength.UNKNOWN: "❓"
        }[self]
    
    @property
    def is_allowed(self) -> bool:
        """Whether this strength is allowed in connections view."""
        # INFERRED connections are not allowed - they belong in patterns view
        return self != ConnectionStrength.INFERRED


@dataclass(frozen=True)
class ConnectionEndpoint:
    """One end of a connection."""
    id: str
    type: str  # "observation", "note", "file", "directory"
    display_name: str
    location: Optional[str] = None  # Path, line number, etc.
    
    def __post_init__(self) -> None:
        """Validate endpoint invariants."""
        if not self.id.strip():
            raise ValueError("Connection endpoint must have ID")
        
        if not self.type.strip():
            raise ValueError("Connection endpoint must have type")
        
        if not self.display_name.strip():
            raise ValueError("Connection endpoint must have display name")


@dataclass(frozen=True)
class DeclaredConnection:
    """
    Immutable declared connection between endpoints.
    
    Article 10: Must have clear origin and evidence.
    Article 11: Must declare what cannot be inferred.
    """
    id: str
    connection_type: ConnectionType
    from_endpoint: ConnectionEndpoint
    to_endpoint: ConnectionEndpoint
    
    # Evidence and origin
    evidence: str                    # What proves this connection exists
    origin: str                     # Where this connection was declared
    
    # Properties of the connection
    strength: ConnectionStrength = ConnectionStrength.EXPLICIT
    directionality: str = "bidirectional"  # "unidirectional", "bidirectional"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Metadata about the declaration
    declared_by: Optional[str] = None  # Who/what declared it
    declaration_context: Optional[str] = None
    
    # Limitations (Article 11)
    cannot_infer: Tuple[str, ...] = field(default_factory=tuple)
    declared_limitations: Tuple[str, ...] = field(default_factory=tuple)
    
    def __post_init__(self) -> None:
        """Validate connection invariants."""
        if not self.evidence.strip():
            raise ValueError("Connection must have evidence")
        
        if not self.origin.strip():
            raise ValueError("Connection must have origin")
        
        # Check that strength is allowed
        if not self.strength.is_allowed:
            raise ValueError(f"Connection strength {self.strength} not allowed in connections view")
        
        # Ensure timestamp is timezone aware
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, 'timestamp',
                             self.timestamp.replace(tzinfo=timezone.utc))
        
        # Check for inference markers in evidence
        inference_indicators = ["implies", "suggests", "probably", "likely", "seems"]
        evidence_lower = self.evidence.lower()
        for indicator in inference_indicators:
            if indicator in evidence_lower:
                raise ValueError(f"Connection evidence contains inference: '{indicator}'")
    
    @property
    def is_human_declared(self) -> bool:
        """Whether this connection was declared by a human."""
        return self.connection_type == ConnectionType.HUMAN_DECLARED
    
    @property
    def is_source_declared(self) -> bool:
        """Whether this connection was declared in source code."""
        return self.connection_type == ConnectionType.SOURCE_DECLARED
    
    @property
    def has_limitations(self) -> bool:
        """Whether this connection has declared limitations."""
        return bool(self.cannot_infer) or bool(self.declared_limitations)


@dataclass(frozen=True)
class ConnectionGroup:
    """Group of connections for display."""
    group_key: str
    group_type: str  # "by_endpoint", "by_connection_type", "by_strength"
    connections: Tuple[DeclaredConnection, ...]
    
    def __post_init__(self) -> None:
        """Validate group invariants."""
        if not self.group_key.strip():
            raise ValueError("Connection group must have a key")
        
        if not self.group_type.strip():
            raise ValueError("Connection group must have a type")
        
        if len(self.connections) == 0:
            raise ValueError("Connection group must contain connections")
    
    @property
    def count(self) -> int:
        """Number of connections in this group."""
        return len(self.connections)
    
    @property
    def from_endpoints(self) -> FrozenSet[str]:
        """Unique 'from' endpoints in this group."""
        return frozenset(conn.from_endpoint.id for conn in self.connections)
    
    @property
    def to_endpoints(self) -> FrozenSet[str]:
        """Unique 'to' endpoints in this group."""
        return frozenset(conn.to_endpoint.id for conn in self.connections)
    
    @property
    def all_endpoints(self) -> FrozenSet[str]:
        """All unique endpoints in this group."""
        endpoints = set()
        for conn in self.connections:
            endpoints.add(conn.from_endpoint.id)
            endpoints.add(conn.to_endpoint.id)
        return frozenset(endpoints)


class ConnectionsDisplayMode(Enum):
    """How connections should be displayed."""
    BY_ENDPOINT = auto()       # Grouped by endpoint (what connects to what)
    BY_TYPE = auto()           # Grouped by connection type
    BY_STRENGTH = auto()       # Grouped by connection strength
    CHRONOLOGICAL = auto()     # By declaration time
    UNSTRUCTURED = auto()      # Simple list


@dataclass(frozen=True)
class ConnectionsRenderConfig:
    """
    Configuration for connections rendering.
    
    Article 10: Must show origin of connections
    Article 11: Must show limitations
    Article 16: Must be clear and readable
    """
    display_mode: ConnectionsDisplayMode = ConnectionsDisplayMode.BY_ENDPOINT
    max_connections_displayed: int = 30           # Prevent overwhelm
    show_evidence: bool = True                    # Always show what proves connection
    show_origin: bool = True                      # Always show where from
    show_limitations: bool = True                 # Show what cannot be inferred
    group_collapsed_by_default: bool = False      # Progressive disclosure
    highlight_current_focus: bool = True          # Connections involving current focus
    
    @classmethod
    def default(cls) -> ConnectionsRenderConfig:
        """Default configuration adhering to constitutional rules."""
        return cls()


class ConnectionsView:
    """
    Deterministic projection from declared connections → relationship display.
    
    Core Responsibility:
    Display explicitly stated connections, not inferred ones.
    
    This view shows what has been asserted, not what has been discovered.
    
    What this view MAY SHOW:
    1. Human-declared links
    2. Source-declared relationships
    3. Temporal adjacency
    4. Structural references
    
    What this view MUST NOT SHOW:
    1. Correlations ❌
    2. Causation ❌
    3. Network centrality ❌
    4. Graph analytics ❌
    
    If the system didn't explicitly record the connection, it does not belong here.
    
    Mental Model: Footnotes and citations, not a theory.
    """
    
    # Display constants
    _DIRECTION_ICONS: ClassVar[Dict[str, str]] = {
        "unidirectional": "→",
        "bidirectional": "↔"
    }
    
    def __init__(
        self,
        context: SessionContext,
        connections: Tuple[DeclaredConnection, ...],
        config: Optional[ConnectionsRenderConfig] = None
    ) -> None:
        """
        Initialize connections view with declared connections.
        
        Args:
            context: Read-only investigation context
            connections: Immutable declared connections
            config: Optional rendering configuration
        
        Raises:
            ValueError: If connections contain inference
            TypeError: If connections are not DeclaredConnection instances
        """
        # Validate inputs
        if not isinstance(context, SessionContext):
            raise TypeError(f"context must be SessionContext, got {type(context)}")
        
        # Validate that connections are truly declared, not inferred
        self._validate_connections_are_declared(connections)
        
        # Store read-only state
        self._context: SessionContext = context
        self._connections: Tuple[DeclaredConnection, ...] = connections
        self._config: ConnectionsRenderConfig = config or ConnectionsRenderConfig.default()
        
        # Apply philosophy rules
        self._apply_philosophy_rules()
    
    def _validate_connections_are_declared(self, connections: Tuple[DeclaredConnection, ...]) -> None:
        """
        Validate that connections are explicitly declared.
        
        This is a critical safety check.
        If connections contain inference markers, reject them.
        """
        for conn in connections:
            # Check type
            if not isinstance(conn, DeclaredConnection):
                raise TypeError(f"Connection must be DeclaredConnection, got {type(conn)}")
            
            # Check for inference
            if conn.strength == ConnectionStrength.INFERRED:
                raise ValueError(f"Connection {conn.id} has INFERRED strength - not allowed")
            
            # Check evidence for inference language
            inference_indicators = [
                "correlates", "associated", "related", "linked by pattern",
                "statistically", "tends to", "often", "usually"
            ]
            evidence_lower = conn.evidence.lower()
            for indicator in inference_indicators:
                if indicator in evidence_lower:
                    raise ValueError(f"Connection evidence contains inference: '{indicator}'")
            
            # Check that origin is explicit
            vague_origins = ["analysis", "detection", "pattern", "heuristic", "algorithm"]
            origin_lower = conn.origin.lower()
            for vague in vague_origins:
                if vague in origin_lower:
                    raise ValueError(f"Connection origin is vague: '{vague}'")
    
    def _apply_philosophy_rules(self) -> None:
        """Apply lens philosophy rules to this view."""
        # Article 5: Single-Focus Interface
        SingleFocusRule.enforce("connections")
        
        # Article 6: Linear Investigation
        # Connections come after examination, before thinking
        
        # Article 7: Clear Affordances
        # Show declared connections, no connection discovery
        
        # Article 8: Honest Performance
        # If there are no connections, say so clearly
    
    def render(self) -> Dict[str, Any]:
        """
        Render connections for display.
        
        This method is DETERMINISTIC and PURE:
        Same context + connections + config = same output.
        No inference, no discovery, no graph analysis.
        
        Returns:
            Structured data ready for display layer
        """
        if not self._connections:
            return self._render_empty_state()
        
        # Apply display mode to organize connections
        organized = self._organize_connections()
        
        # Apply display rules (presentation only)
        rendered = self._apply_display_rules(organized)
        
        # Add metadata and warnings
        rendered.update(self._get_view_metadata())
        
        return rendered
    
    def _organize_connections(self) -> Dict[str, Any]:
        """
        Organize connections according to display mode.
        
        This is PURE ORGANIZATION only:
        - Group by explicit, pre-defined categories
        - Sort by explicit criteria
        - No inference of relationships beyond what's declared
        
        If you find yourself computing graph properties, STOP.
        That's a constitutional violation.
        """
        mode = self._config.display_mode
        
        if mode == ConnectionsDisplayMode.BY_ENDPOINT:
            return self._organize_by_endpoint()
        elif mode == ConnectionsDisplayMode.BY_TYPE:
            return self._organize_by_type()
        elif mode == ConnectionsDisplayMode.BY_STRENGTH:
            return self._organize_by_strength()
        elif mode == ConnectionsDisplayMode.CHRONOLOGICAL:
            return self._organize_chronologically()
        elif mode == ConnectionsDisplayMode.UNSTRUCTURED:
            return self._organize_unstructured()
        else:
            raise ValueError(f"Unknown display mode: {mode}")
    
    def _organize_by_endpoint(self) -> Dict[str, Any]:
        """Organize connections by endpoint (what connects to what)."""
        # Group by from_endpoint
        groups_by_from: Dict[str, List[DeclaredConnection]] = defaultdict(list)
        
        for conn in self._connections:
            groups_by_from[conn.from_endpoint.id].append(conn)
        
        # Create groups
        groups: List[ConnectionGroup] = []
        for endpoint_id in sorted(groups_by_from.keys()):
            endpoint_conns = groups_by_from[endpoint_id]
            
            # Sort by to_endpoint for consistency
            sorted_conns = sorted(endpoint_conns, 
                                key=lambda c: c.to_endpoint.display_name)
            
            # Apply per-group limit
            display_conns = sorted_conns[:self._config.max_connections_displayed]
            
            groups.append(ConnectionGroup(
                group_key=endpoint_id,
                group_type="by_endpoint",
                connections=tuple(display_conns)
            ))
        
        return {
            "organization": "by_endpoint",
            "groups": groups,
            "endpoint_count": len(groups_by_from)
        }
    
    def _organize_by_type(self) -> Dict[str, Any]:
        """Organize connections by connection type."""
        groups_by_type: Dict[ConnectionType, List[DeclaredConnection]] = defaultdict(list)
        
        for conn in self._connections:
            groups_by_type[conn.connection_type].append(conn)
        
        # Create groups
        groups: List[ConnectionGroup] = []
        for conn_type in ConnectionType:
            if conn_type in groups_by_type:
                type_conns = groups_by_type[conn_type]
                
                # Sort by timestamp for consistency
                sorted_conns = sorted(type_conns, 
                                    key=lambda c: c.timestamp, 
                                    reverse=True)
                
                # Apply per-group limit
                display_conns = sorted_conns[:self._config.max_connections_displayed]
                
                groups.append(ConnectionGroup(
                    group_key=conn_type.name,
                    group_type="by_type",
                    connections=tuple(display_conns)
                ))
        
        return {
            "organization": "by_type",
            "groups": groups,
            "type_count": len(groups_by_type)
        }
    
    def _organize_by_strength(self) -> Dict[str, Any]:
        """Organize connections by connection strength."""
        groups_by_strength: Dict[ConnectionStrength, List[DeclaredConnection]] = defaultdict(list)
        
        for conn in self._connections:
            groups_by_strength[conn.strength].append(conn)
        
        # Create groups
        groups: List[ConnectionGroup] = []
        for strength in ConnectionStrength:
            if strength in groups_by_strength:
                strength_conns = groups_by_strength[strength]
                
                # Sort by type for consistency
                sorted_conns = sorted(strength_conns, 
                                    key=lambda c: c.connection_type.name)
                
                # Apply per-group limit
                display_conns = sorted_conns[:self._config.max_connections_displayed]
                
                groups.append(ConnectionGroup(
                    group_key=strength.name,
                    group_type="by_strength",
                    connections=tuple(display_conns)
                ))
        
        return {
            "organization": "by_strength",
            "groups": groups,
            "strength_count": len(groups_by_strength)
        }
    
    def _organize_chronologically(self) -> Dict[str, Any]:
        """Organize connections by declaration time."""
        # Sort by timestamp (most recent first)
        sorted_conns = sorted(self._connections, 
                            key=lambda c: c.timestamp, 
                            reverse=True)
        
        # Apply display limit
        display_conns = sorted_conns[:self._config.max_connections_displayed]
        
        return {
            "organization": "chronological",
            "groups": [
                ConnectionGroup(
                    group_key="chronological",
                    group_type="time_based",
                    connections=tuple(display_conns)
                )
            ],
            "time_range": {
                "earliest": sorted_conns[-1].timestamp.isoformat() if sorted_conns else None,
                "latest": sorted_conns[0].timestamp.isoformat() if sorted_conns else None
            }
        }
    
    def _organize_unstructured(self) -> Dict[str, Any]:
        """Show connections as a simple list."""
        # No sorting, just raw order (but limited)
        display_conns = self._connections[:self._config.max_connections_displayed]
        
        return {
            "organization": "unstructured",
            "groups": [
                ConnectionGroup(
                    group_key="all_connections",
                    group_type="unstructured",
                    connections=tuple(display_conns)
                )
            ]
        }
    
    def _prepare_connection_display(self, conn: DeclaredConnection) -> Dict[str, Any]:
        """
        Prepare a declared connection for display.
        
        This adds display annotations but NO interpretation.
        Every field must come directly from the connection.
        
        Article 10: Must show origin and evidence.
        Article 11: Must show limitations.
        """
        display: Dict[str, Any] = {
            "id": conn.id,
            "type": conn.connection_type.name,
            "type_display": conn.connection_type.display_name,
            "type_icon": conn.connection_type.icon,
            "strength": conn.strength.name,
            "strength_display": conn.strength.display_symbol,
            "directionality": conn.directionality,
            "direction_icon": self._DIRECTION_ICONS.get(conn.directionality, "↔")
        }
        
        # Endpoints
        display["from_endpoint"] = {
            "id": conn.from_endpoint.id,
            "type": conn.from_endpoint.type,
            "display_name": conn.from_endpoint.display_name,
            "location": conn.from_endpoint.location
        }
        
        display["to_endpoint"] = {
            "id": conn.to_endpoint.id,
            "type": conn.to_endpoint.type,
            "display_name": conn.to_endpoint.display_name,
            "location": conn.to_endpoint.location
        }
        
        # Evidence and origin (Article 10)
        if self._config.show_evidence:
            display["evidence"] = conn.evidence
        
        if self._config.show_origin:
            display["origin"] = conn.origin
        
        # Metadata
        display["timestamp"] = conn.timestamp.isoformat()
        if conn.declared_by:
            display["declared_by"] = conn.declared_by
        if conn.declaration_context:
            display["declaration_context"] = conn.declaration_context
        
        # Limitations (Article 11)
        if self._config.show_limitations and conn.has_limitations:
            display["limitations"] = {
                "cannot_infer": list(conn.cannot_infer),
                "declared_limitations": list(conn.declared_limitations)
            }
        
        # Highlight if involves current focus
        if (self._config.highlight_current_focus and 
            self._context.current_focus):
            focus_id = self._context.current_focus
            if (focus_id in [conn.from_endpoint.id, conn.to_endpoint.id] or
                (conn.from_endpoint.location and focus_id in conn.from_endpoint.location) or
                (conn.to_endpoint.location and focus_id in conn.to_endpoint.location)):
                display["involves_current_focus"] = True
        
        return display
    
    def _prepare_group_display(self, group: ConnectionGroup) -> Dict[str, Any]:
        """Prepare a connection group for display."""
        display: Dict[str, Any] = {
            "group_key": group.group_key,
            "group_type": group.group_type,
            "connection_count": group.count,
            "connections": [self._prepare_connection_display(conn) for conn in group.connections],
            "is_collapsed": self._config.group_collapsed_by_default
        }
        
        # Add group-specific metadata
        if group.group_type == "by_endpoint":
            display["from_endpoint"] = group.group_key
        
        return display
    
    def _apply_display_rules(self, organized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply display rules to organized connections.
        
        This ensures the view adheres to:
        - Article 10: Anchored Thinking (clear origins)
        - Article 11: Declared Limitations
        - Article 16: Truth-Preserving Aesthetics
        """
        result = organized.copy()
        
        # Add view type identifier
        result["view_type"] = "connections"
        result["view_philosophy"] = "declared_relationships_only"
        
        # Apply progressive disclosure: show if there's more
        total_connections = len(self._connections)
        displayed_count = sum(len(g.connections) for g in organized.get("groups", []))
        
        result["display_stats"] = {
            "total_available": total_connections,
            "displayed": displayed_count,
            "hidden": total_connections - displayed_count,
            "reason_for_hiding": f"Limited to {self._config.max_connections_displayed} per group" 
                                 if displayed_count < total_connections else None
        }
        
        # Apply clarity rule: explain what's being shown
        result["clarity_notes"] = [
            "Showing only explicitly declared connections",
            "No inferred, correlated, or discovered connections",
            "Each connection must have clear evidence and origin"
        ]
        
        # Apply single focus: indicate primary organization
        result["focus"] = organized.get("organization", "unorganized")
        
        # Prepare groups for display
        if "groups" in organized:
            result["display_groups"] = [
                self._prepare_group_display(group) 
                for group in organized["groups"]
            ]
        
        # Add warnings if evidence or origin is hidden
        if not self._config.show_evidence:
            result["warnings"] = ["Evidence for connections is hidden"]
        
        if not self._config.show_origin:
            if "warnings" not in result:
                result["warnings"] = []
            result["warnings"].append("Origin of connections is hidden")
        
        # Add declaration statistics
        declaration_stats = self._calculate_declaration_stats()
        result["declaration_stats"] = declaration_stats
        
        return result
    
    def _calculate_declaration_stats(self) -> Dict[str, Any]:
        """Calculate statistics about how connections were declared."""
        stats = {
            "total": len(self._connections),
            "by_type": defaultdict(int),
            "by_strength": defaultdict(int),
            "human_declared": 0,
            "source_declared": 0
        }
        
        for conn in self._connections:
            stats["by_type"][conn.connection_type.name] += 1
            stats["by_strength"][conn.strength.name] += 1
            
            if conn.is_human_declared:
                stats["human_declared"] += 1
            
            if conn.is_source_declared:
                stats["source_declared"] += 1
        
        # Convert defaultdicts to regular dicts
        stats["by_type"] = dict(stats["by_type"])
        stats["by_strength"] = dict(stats["by_strength"])
        
        return stats
    
    def _render_empty_state(self) -> Dict[str, Any]:
        """
        Render the view when no connections are present.
        
        Article 3: Must be honest about absence.
        Article 8: Must explain why nothing is shown.
        """
        return {
            "view_type": "connections",
            "state": "empty",
            "message": "No declared connections available.",
            "possible_reasons": [
                "No connections have been explicitly declared",
                "Connections were filtered out",
                "The current focus has no declared connections"
            ],
            "important_note": "This view only shows EXPLICITLY DECLARED connections. "
                            "Inferred, correlated, or discovered connections are not shown here.",
            "suggestions": [
                "Declare explicit connections in notes",
                "Look for source-declared connections (imports, references)",
                "Check other views for different types of relationships"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "current_focus": self._context.current_focus,
                "investigation_path": self._context.investigation_path
            }
        }
    
    def _get_view_metadata(self) -> Dict[str, Any]:
        """Get metadata about this view rendering."""
        return {
            "metadata": {
                "rendered_at": datetime.now(timezone.utc).isoformat(),
                "total_connections": len(self._connections),
                "config": asdict(self._config),
                "philosophy_rules_applied": [
                    "SingleFocusRule",
                    "ProgressiveDisclosureRule",
                    "ClarityRule",
                    "NavigationRule"
                ],
                "constitutional_guarantees": [
                    "Article 3: Truth Preservation (no invented connections)",
                    "Article 10: Anchored Thinking (clear origins)",
                    "Article 11: Declared Limitations"
                ],
                "integrity_checks": self._run_integrity_checks()
            }
        }
    
    def _run_integrity_checks(self) -> Dict[str, bool]:
        """Run integrity checks on the view."""
        checks = {
            "no_inference_shown": True,
            "no_graph_analysis": True,
            "evidence_shown": self._config.show_evidence,
            "origin_shown": self._config.show_origin,
            "limitations_shown": self._config.show_limitations
        }
        
        # Check that no connections are inferred
        for conn in self._connections[:10]:  # Sample check
            if conn.strength == ConnectionStrength.INFERRED:
                checks["no_inference_shown"] = False
            
            # Check evidence for inference language
            inference_words = ["correlate", "associate", "pattern", "likely", "probably"]
            for word in inference_words:
                if word in conn.evidence.lower():
                    checks["no_inference_shown"] = False
        
        return checks
    
    def validate_integrity(self) -> List[str]:
        """
        Validate that this view adheres to truth-preserving constraints.
        
        Returns:
            List of violations (empty if valid)
        """
        violations = []
        
        # Check 1: No inference shown
        for conn in self._connections:
            if conn.strength == ConnectionStrength.INFERRED:
                violations.append(f"Connection {conn.id} has INFERRED strength")
            
            # Check evidence
            inference_indicators = [
                "correlation", "association", "tends to", "often", "usually",
                "pattern suggests", "likely connected", "probably related"
            ]
            for indicator in inference_indicators:
                if indicator in conn.evidence.lower():
                    violations.append(f"Connection {conn.id} evidence contains inference: '{indicator}'")
        
        # Check 2: No graph analysis
        # Look for any graph theory concepts in display
        graph_concepts = ["centrality", "degree", "clustering", "path", "network"]
        rendered = self.render()
        rendered_str = str(rendered).lower()
        for concept in graph_concepts:
            if concept in rendered_str:
                violations.append(f"View contains graph analysis concept: '{concept}'")
        
        # Check 3: All connections must have evidence and origin
        for conn in self._connections:
            if not conn.evidence.strip():
                violations.append(f"Connection {conn.id} has no evidence")
            
            if not conn.origin.strip():
                violations.append(f"Connection {conn.id} has no origin")
        
        # Check 4: Must show limitations if present
        connections_with_limitations = [c for c in self._connections if c.has_limitations]
        if connections_with_limitations and not self._config.show_limitations:
            violations.append(f"{len(connections_with_limitations)} connections have limitations but they are hidden")
        
        # Check 5: No causation implied
        causation_words = ["causes", "leads to", "results in", "because", "therefore"]
        for conn in self._connections:
            for word in causation_words:
                if word in conn.evidence.lower():
                    violations.append(f"Connection {conn.id} implies causation: '{word}'")
        
        return violations
    
    def get_connections_involving(self, endpoint_id: str) -> Tuple[DeclaredConnection, ...]:
        """
        Get all connections involving a specific endpoint.
        
        This is a pure filter operation, not graph traversal.
        
        Args:
            endpoint_id: ID of endpoint to find connections for
        
        Returns:
            Connections where endpoint appears as from or to
        """
        result: List[DeclaredConnection] = []
        
        for conn in self._connections:
            if (conn.from_endpoint.id == endpoint_id or 
                conn.to_endpoint.id == endpoint_id):
                result.append(conn)
        
        return tuple(result)
    
    def get_endpoint_summary(self, endpoint_id: str) -> Dict[str, Any]:
        """
        Get summary of connections for an endpoint.
        
        This is NOT graph analysis - just counting and listing.
        
        Args:
            endpoint_id: ID of endpoint to summarize
        
        Returns:
            Simple counts and lists of connections
        """
        connections = self.get_connections_involving(endpoint_id)
        
        from_count = 0
        to_count = 0
        
        for conn in connections:
            if conn.from_endpoint.id == endpoint_id:
                from_count += 1
            if conn.to_endpoint.id == endpoint_id:
                to_count += 1
        
        return {
            "endpoint_id": endpoint_id,
            "total_connections": len(connections),
            "from_count": from_count,
            "to_count": to_count,
            "connection_types": {
                conn_type.name: sum(1 for c in connections if c.connection_type == conn_type)
                for conn_type in ConnectionType
            }
        }
    
    @classmethod
    def create_test_view(cls) -> ConnectionsView:
        """
        Create a test view for development and testing.
        
        Returns:
            A ConnectionsView with test data
        """
        from datetime import datetime, timedelta
        
        # Create test context
        class TestContext(InvestigationContext):
            def __init__(self) -> None:
                self.current_focus = "obs:import:1"
                self.investigation_path = ["started", "examining_connections"]
                self.created_at = datetime.now(timezone.utc)
        
        # Create test connections
        now = datetime.now(timezone.utc)
        
        # Connection 1: Note anchored to observation
        conn1 = DeclaredConnection(
            id="conn:note_anchor:1",
            connection_type=ConnectionType.NOTE_ANCHOR,
            from_endpoint=ConnectionEndpoint(
                id="note:thinking:1",
                type="note",
                display_name="Thought about imports",
                location="notebook:personal"
            ),
            to_endpoint=ConnectionEndpoint(
                id="obs:import:1",
                type="observation",
                display_name="Import statement",
                location="example.py:10"
            ),
            evidence="Note explicitly references observation ID",
            origin="User created note with anchor",
            strength=ConnectionStrength.EXPLICIT,
            directionality="unidirectional",
            timestamp=now - timedelta(hours=2),
            declared_by="user:alice",
            declaration_context="Thinking about architecture",
            cannot_infer=("Cannot infer semantic meaning", "Cannot infer importance"),
            declared_limitations=("Only shows explicit anchor", "Does not show if note understands observation")
        )
        
        # Connection 2: Source-declared import
        conn2 = DeclaredConnection(
            id="conn:source:1",
            connection_type=ConnectionType.SOURCE_DECLARED,
            from_endpoint=ConnectionEndpoint(
                id="file:example.py",
                type="file",
                display_name="example.py",
                location="/project/example.py"
            ),
            to_endpoint=ConnectionEndpoint(
                id="module:os",
                type="module",
                display_name="os module",
                location="Python standard library"
            ),
            evidence="Line 1: 'import os'",
            origin="Source code text",
            strength=ConnectionStrength.EXPLICIT,
            directionality="unidirectional",
            timestamp=now - timedelta(hours=1, minutes=45),
            declared_by="compiler",
            declaration_context="Static analysis"
        )
        
        # Connection 3: Structural containment
        conn3 = DeclaredConnection(
            id="conn:structural:1",
            connection_type=ConnectionType.STRUCTURAL_CONTAINMENT,
            from_endpoint=ConnectionEndpoint(
                id="dir:/project",
                type="directory",
                display_name="/project",
                location="/project"
            ),
            to_endpoint=ConnectionEndpoint(
                id="file:example.py",
                type="file",
                display_name="example.py",
                location="/project/example.py"
            ),
            evidence="File exists in directory",
            origin="Filesystem hierarchy",
            strength=ConnectionStrength.EXPLICIT,
            directionality="unidirectional",
            timestamp=now - timedelta(hours=1, minutes=30)
        )
        
        # Connection 4: Temporal adjacency
        conn4 = DeclaredConnection(
            id="conn:temporal:1",
            connection_type=ConnectionType.TEMPORAL_ADJACENCY,
            from_endpoint=ConnectionEndpoint(
                id="obs:import:1",
                type="observation",
                display_name="First import observation",
                location="example.py:1"
            ),
            to_endpoint=ConnectionEndpoint(
                id="obs:import:2",
                type="observation",
                display_name="Second import observation",
                location="example.py:5"
            ),
            evidence="Observations recorded within 5 seconds of each other",
            origin="Observation timestamps",
            strength=ConnectionStrength.WEAK,
            directionality="bidirectional",
            timestamp=now - timedelta(hours=1),
            cannot_infer=("Cannot infer logical connection", "Cannot infer dependency")
        )
        
        # Connection 5: Human declared relationship
        conn5 = DeclaredConnection(
            id="conn:human:1",
            connection_type=ConnectionType.HUMAN_DECLARED,
            from_endpoint=ConnectionEndpoint(
                id="concept:boundary_violation",
                type="concept",
                display_name="Boundary violation",
                location="architectural_rules.md"
            ),
            to_endpoint=ConnectionEndpoint(
                id="obs:import:cross_lobe",
                type="observation",
                display_name="Cross-lobe import",
                location="module_x.py:42"
            ),
            evidence="Architect wrote: 'This import violates lobe boundaries'",
            origin="Architectural review notes",
            strength=ConnectionStrength.EXPLICIT,
            directionality="unidirectional",
            timestamp=now - timedelta(minutes=45),
            declared_by="architect:charlie",
            declaration_context="Code review session",
            declared_limitations=("Only one person's opinion", "Needs verification")
        )
        
        return cls(
            TestContext(),
            (conn1, conn2, conn3, conn4, conn5)
        )


def main() -> None:
    """Test the connections view."""
    view = ConnectionsView.create_test_view()
    
    # Test different display modes
    for mode in ConnectionsDisplayMode:
        print(f"\n=== {mode.name} ===")
        config = ConnectionsRenderConfig(display_mode=mode)
        test_view = ConnectionsView(view._context, view._connections, config)
        rendered = test_view.render()
        print(json.dumps(rendered, indent=2, default=str))
    
    # Validate integrity
    violations = view.validate_integrity()
    if violations:
        print(f"\nINTEGRITY VIOLATIONS ({len(violations)}):")
        for violation in violations:
            print(f"  ⚠️  {violation}")
    else:
        print("\n✅ View passes integrity checks.")
    
    # Test endpoint summary
    print("\n=== ENDPOINT SUMMARY ===")
    summary = view.get_endpoint_summary("obs:import:1")
    print(json.dumps(summary, indent=2, default=str))
    
    # Test empty state
    print("\n=== EMPTY STATE TEST ===")
    empty_view = ConnectionsView(view._context, tuple())
    empty_rendered = empty_view.render()
    print(json.dumps(empty_rendered, indent=2, default=str))


if __name__ == "__main__":
    main()