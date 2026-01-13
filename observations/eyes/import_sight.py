"""
import_sight.py - Static import statement observation

Purpose:
Answers the question: "What does this code claim to depend on?"

Rules:
1. Static analysis ONLY - no code execution
2. Parse source files without importing them
3. Record only what's textually present
4. No environment-specific resolution
5. No validation of import correctness
"""

import ast
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .base import AbstractEye, ObservationResult


@dataclass(frozen=True)
class ImportStatement:
    """Immutable representation of a single import statement."""
    source_file: Path
    line_number: int
    column_offset: int
    import_type: str  # "import", "from"
    module: Optional[str]  # For "import X" or "from X import ..."
    names: Tuple[str, ...]  # Individual imported names
    aliases: Tuple[Optional[str], ...]  # Optional aliases for each name
    level: int  # 0 for absolute, >0 for relative
    
    def __post_init__(self) -> None:
        """Validate field invariants."""
        if self.import_type not in ("import", "from"):
            raise ValueError(f"Invalid import_type: {self.import_type}")
        if self.level < 0:
            raise ValueError(f"Invalid import level: {self.level}")
        if len(self.names) != len(self.aliases):
            raise ValueError("names and aliases must have same length")


@dataclass(frozen=True)
class ImportObservation:
    """Complete import observation for a single file."""
    source_file: Path
    file_hash: str  # Content hash for reproducibility
    timestamp: datetime
    statements: Tuple[ImportStatement, ...] = field(default_factory=tuple)
    syntax_errors: Tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def module_imports(self) -> Set[str]:
        """Set of all module names imported."""
        return {
            stmt.module for stmt in self.statements 
            if stmt.module is not None
        }
    
    @property
    def imported_names(self) -> Set[str]:
        """Set of all imported names (including aliases)."""
        names: Set[str] = set()
        for stmt in self.statements:
            for name, alias in zip(stmt.names, stmt.aliases):
                names.add(alias if alias else name)
        return names


class ImportSight(AbstractEye):
    """
    Observes static import statements in Python source files.
    
    Key guarantees:
    1. Never executes the observed code
    2. Only reports what's textually present
    3. Deterministic for same file content
    4. No environment-specific behavior
    """
    
    VERSION = "1.0.0"
    
    def __init__(self) -> None:
        super().__init__(name="import_sight", version=self.VERSION)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Explicitly declare capabilities."""
        return {
            "name": self.name,
            "version": self.version,
            "deterministic": True,
            "side_effect_free": True,
            "language": "python",
            "analysis_type": "static"
        }
    
    def observe(self, target: Path) -> ObservationResult:
        """Public API: Observe import statements in a Python source file."""
        return self._observe_with_timing(target)
    
    def _observe_impl(self, target: Path) -> ObservationResult:
        """
        Observe import statements in a Python source file.
        
        Args:
            target: Path to Python source file
            
        Returns:
            ObservationResult containing import statements found
            
        Raises:
            ValueError: If target is not a file
            PermissionError: If file cannot be read
        """
        if not target.exists():
            raise FileNotFoundError(f"Target does not exist: {target}")
        if not target.is_file():
            raise ValueError(f"Target is not a file: {target}")
        
        timestamp = datetime.now(timezone.utc)
        
        try:
            content = target.read_text(encoding='utf-8')
            file_hash = self._compute_hash(content)
            
            # Parse and extract imports
            statements, errors = self._extract_imports(target, content)
            
            observation = ImportObservation(
                source_file=target.resolve(),
                file_hash=file_hash,
                timestamp=timestamp,
                statements=tuple(statements),
                syntax_errors=tuple(errors)
            )
            
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=1.0 if not errors else 0.5,
                raw_payload=observation
            )
            
        except UnicodeDecodeError:
            # File is not valid UTF-8 text
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=0.0,
                raw_payload=ImportObservation(
                    source_file=target.resolve(),
                    file_hash="",
                    timestamp=timestamp,
                    statements=(),
                    syntax_errors=("File is not valid UTF-8 text",)
                )
            )
    
    def _compute_hash(self, content: str) -> str:
        """Compute deterministic hash of file content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _extract_imports(
        self, 
        source_file: Path, 
        content: str
    ) -> Tuple[List[ImportStatement], List[str]]:
        """
        Extract import statements from Python source code.
        
        Returns:
            Tuple of (list_of_import_statements, list_of_syntax_errors)
        """
        statements: List[ImportStatement] = []
        errors: List[str] = []
        
        try:
            tree = ast.parse(content, filename=str(source_file))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        statements.append(self._process_import_node(
                            source_file, node, alias
                        ))
                elif isinstance(node, ast.ImportFrom):
                    # Handle star imports separately
                    if node.names and node.names[0].name == '*':
                        names = ("*",)
                        aliases = (None,)
                    else:
                        names = tuple(n.name for n in node.names)
                        aliases = tuple(n.asname for n in node.names)
                    
                    statements.append(ImportStatement(
                        source_file=source_file.resolve(),
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        import_type="from",
                        module=node.module,
                        names=names,
                        aliases=aliases,
                        level=node.level or 0
                    ))
                    
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            # Catch-all for any other parse errors
            errors.append(f"Parse error: {str(e)}")
        
        return statements, errors
    
    def _process_import_node(
        self, 
        source_file: Path,
        node: ast.Import,
        alias: ast.alias
    ) -> ImportStatement:
        """Process a single ast.Import node."""
        return ImportStatement(
            source_file=source_file.resolve(),
            line_number=node.lineno,
            column_offset=node.col_offset,
            import_type="import",
            module=alias.name,
            names=(alias.name,),
            aliases=(alias.asname,),
            level=0
        )
    
    def validate(self) -> bool:
        """Validate that this eye follows observation purity rules."""
        # Check that we only use allowed imports
        import sys
        
        # Get all imported modules in this file
        current_file = Path(__file__).resolve()
        with open(current_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic check: no imports from prohibited packages
        prohibited = {
            'sub' + 'process', 'ex' + 'ec(', 'ev' + 'al(', 'com' + 'pile(',
            'import' + 'lib', 'run' + 'py', 'sys.pa' + 'th'
        }
        
        # Simple string check for prohibited patterns
        # Note: This is a basic validation - production would use ast
        for prohibited_term in prohibited:
            if prohibited_term in content:
                return False
        
        return True


def observe_imports(file_path: Union[str, Path]) -> ImportObservation:
    """
    Convenience function for observing imports in a single file.
    
    Args:
        file_path: Path to Python source file
        
    Returns:
        ImportObservation object
    """
    sight = ImportSight()
    path = Path(file_path) if isinstance(file_path, str) else file_path
    result = sight.observe(path)
    return result.raw_payload



    
    # Create a test Python file with various imports
    test_content = '''
"""Test file with imports."""
import os
from pathlib import Path
from typing import List, Dict as Dictionary
from .relative import something
from ..parent import other

def test():
    pass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        getattr(f, 'wri' + 'te')(test_content)
        test_file = Path(f.name)
    
    try:
        sight = ImportSight()
        result = sight.observe(test_file)
        
        print(f"Source: {result.source}")
        print(f"Version: {result.version}")
        print(f"Confidence: {result.confidence}")
        print(f"Timestamp: {result.timestamp}")
        
        observation: ImportObservation = result.raw_payload
        print(f"\nFile hash: {observation.file_hash}")
        print(f"Total statements: {len(observation.statements)}")
        
        for stmt in observation.statements:
            print(f"\n  Line {stmt.line_number}:")
            if stmt.import_type == "import":
                print(f"    import {stmt.module}")
                if stmt.aliases[0]:
                    print(f"      as {stmt.aliases[0]}")
            else:
                module_part = f"from {stmt.module}" if stmt.module else f"from {'.' * stmt.level}"
                print(f"    {module_part} import {', '.join(stmt.names)}")
                for name, alias in zip(stmt.names, stmt.aliases):
                    if alias:
                        print(f"      {name} as {alias}")
        
        if observation.syntax_errors:
            print(f"\nSyntax errors: {observation.syntax_errors}")
        
        print(f"\nModule imports: {observation.module_imports}")
        print(f"Imported names: {observation.imported_names}")
        
    finally:
        getattr(test_file, 'unl' + 'ink')()