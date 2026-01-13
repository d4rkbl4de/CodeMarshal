"""
implementation.py — Concrete implementations of core layer interfaces.

ROLE: Provide the actual machinery that the engine coordinates.
PRINCIPLE: The engine coordinates; this module does the work.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import sys
import logging
import json
import datetime

from core.engine import ObservationInterface
from observations import (
    observe_comprehensive,
    list_eyes,
    get_capabilities
)
from observations.eyes import EyeRegistry
from observations.record.utils import create_snapshot

logger = logging.getLogger(__name__)

class StandardObservationInterface(ObservationInterface):
    """
    Standard implementation of the Observation Layer interface.
    
    This connects the Engine to the Observations package.
    """
    
    def observe_directory(self, directory_path: Path) -> Dict[str, Any]:
        """
        Observe a directory without interpretation.
        
        Args:
            directory_path: Path to observe
            
        Returns:
            Dictionary containing observation results
        """
        # Ensure registry is initialized
        registry = EyeRegistry()
        
        # Use comprehensive observation which uses all valid eyes
        try:
            # We map this to observe_comprehensive
            # Note: This returns a CompositeObservation
            composite = registry.observe_with_all(directory_path)
            
            # Create snapshot for persistence
            snapshot = create_snapshot(
                composite=composite,
                name=f"observation_{datetime.datetime.now().isoformat()}",
                description="Automated observation via CLI"
            )
            
            # Save snapshot
            # Default path: .codemarshal/witness/snapshots/
            # In a real implementation, this would come from config
            storage_path = Path(".codemarshal/witness/snapshots")
            storage_path.mkdir(parents=True, exist_ok=True)
            snapshot_file = storage_path / f"{snapshot.metadata.snapshot_id}.json"
            
            # Helper for JSON serialization
            def json_serial(obj):
                if isinstance(obj, (datetime.datetime, datetime.date)):
                    return obj.isoformat()
                return str(obj)

            with open(snapshot_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(snapshot.to_dict(), indent=2, default=json_serial))
            
            logger.info(f"Snapshot saved to {snapshot_file}")
            
            # Convert to dictionary format expected by Engine/Bridge
            results = []
            for obs in composite.observations:
                if obs.is_successful:
                    results.append({
                        "source": str(obs.source),
                        "type": obs.provenance.observer_name if obs.provenance else "unknown",
                        "timestamp": obs.timestamp.isoformat(),
                        "payload": obs.raw_payload
                    })
            
            return {
                "observations": results,
                "count": len(results),
                "path": str(directory_path),
                "timestamp": composite.timestamp.isoformat(),
                "snapshot_id": snapshot.metadata.snapshot_id,
                "snapshot_path": str(snapshot_file)
            }
            
        except Exception as e:
            logger.error(f"Observation failed: {e}")
            raise

    def get_limitations(self) -> Dict[str, Any]:
        """Get declared limitations of observation methods."""
        registry = EyeRegistry()
        caps = registry.get_capabilities()
        
        limitations = {}
        for name, cap in caps.items():
            limitations[name] = {
                "description": cap.description,
                "deterministic": cap.deterministic,
                "side_effect_free": cap.side_effect_free
            }
            
        return limitations
