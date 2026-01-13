"""
export_sight.py - Observation of public definitions and signatures

Purpose:
Answers the question: "What does this module publicly expose?"

Rules:
1. Static analysis ONLY - no code execution
2. Only observe what is textually declared as public
3. No inference about what "should be" public
4. No semantic analysis of definitions
"""

import ast
import inspect
import hashlib
import re
from pathlib import Path
from typing import (
    Any, Dict, List, Optional, Set, Tuple, Union, Iterator,
    NamedTuple, Callable
)
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto

from .base import AbstractEye, ObservationResult


class Visibility(Enum):
    """Visibility classification based on textual declarations."""
    PUBLIC = auto()        # Explicitly in __all__ or starts with letter
    PROTECTED = auto()     # Starts with single underscore _
    PRIVATE = auto()       # Starts with double underscore __
    MODULE_PRIVATE = auto()  # Starts and ends with double underscore __*__


class DefinitionType(Enum):
    """Type of definition observed."""
    FUNCTION = auto()
    CLASS = auto()
    CONSTANT = auto()      # UPPER_CASE assignments
    VARIABLE = auto()      # lower_case assignments
    IMPORT = auto()        # Import statements
    DECORATOR = auto()     # @decorator definitions
    TYPE_ALIAS = auto()    # Type aliases (TypeVar, NewType, etc.)
    UNKNOWN = auto()


@dataclass(frozen=True)
class ParameterInfo:
    """Immutable representation of a function parameter."""
    name: str
    annotation: Optional[str] = None  # Raw string representation
    default: Optional[str] = None     # Raw string representation
    kind: str = "POSITIONAL_OR_KEYWORD"  # POSITIONAL_ONLY, VAR_POSITIONAL, etc.
    
    @property
    def signature_string(self) -> str:
        """String representation of this parameter."""
        parts = [self.name]
        if self.annotation:
            parts.append(f": {self.annotation}")
        if self.default:
            parts.append(f" = {self.default}")
        return "".join(parts)


@dataclass(frozen=True)
class FunctionSignature:
    """Immutable representation of a function signature."""
    name: str
    parameters: Tuple[ParameterInfo, ...] = field(default_factory=tuple)
    returns: Optional[str] = None  # Return annotation as string
    decorators: Tuple[str, ...] = field(default_factory=tuple)
    is_async: bool = False
    is_generator: bool = False  # Contains yield
    source_line: int = 0
    
    @property
    def parameter_count(self) -> int:
        """Total number of parameters."""
        return len(self.parameters)
    
    @property
    def has_defaults(self) -> bool:
        """Whether any parameters have defaults."""
        return any(p.default is not None for p in self.parameters)
    
    def format_signature(self) -> str:
        """Format complete function signature."""
        async_prefix = "async " if self.is_async else ""
        params = ", ".join(p.signature_string for p in self.parameters)
        returns = f" -> {self.returns}" if self.returns else ""
        return f"{async_prefix}def {self.name}({params}){returns}"


@dataclass(frozen=True)
class MethodInfo:
    """Information about a class method."""
    name: str
    signature: FunctionSignature
    visibility: Visibility
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False  # @property decorator
    is_abstract: bool = False  # @abstractmethod or ABC


@dataclass(frozen=True)
class ClassSignature:
    """Immutable representation of a class definition."""
    name: str
    bases: Tuple[str, ...] = field(default_factory=tuple)  # Parent classes
    methods: Tuple[MethodInfo, ...] = field(default_factory=tuple)
    class_attributes: Tuple[str, ...] = field(default_factory=tuple)  # Class-level vars
    decorators: Tuple[str, ...] = field(default_factory=tuple)
    source_line: int = 0
    is_abstract: bool = False  # Contains abstract methods or inherits from ABC
    
    @property
    def public_methods(self) -> Tuple[MethodInfo, ...]:
        """Get all public methods."""
        return tuple(m for m in self.methods if m.visibility == Visibility.PUBLIC)
    
    @property
    def magic_methods(self) -> Tuple[MethodInfo, ...]:
        """Get all dunder methods (__*__)."""
        return tuple(m for m in self.methods if m.name.startswith("__") and m.name.endswith("__"))


@dataclass(frozen=True)
class ExportDefinition:
    """Single definition that can be exported."""
    name: str
    definition_type: DefinitionType
    visibility: Visibility
    signature: Optional[Union[FunctionSignature, ClassSignature]] = None
    source_line: int = 0
    source_column: int = 0
    
    @property
    def is_callable(self) -> bool:
        """Whether this definition is callable (function or method)."""
        return self.definition_type in (DefinitionType.FUNCTION, DefinitionType.CLASS)


@dataclass(frozen=True)
class ModuleExports:
    """Complete export observation for a module."""
    module_path: Path
    file_hash: str
    timestamp: datetime
    explicit_all: Tuple[str, ...] = field(default_factory=tuple)  # Names in __all__
    definitions: Tuple[ExportDefinition, ...] = field(default_factory=tuple)
    errors: Tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def public_definitions(self) -> Tuple[ExportDefinition, ...]:
        """Get all definitions marked as public."""
        return tuple(d for d in self.definitions if d.visibility == Visibility.PUBLIC)
    
    @property
    def private_definitions(self) -> Tuple[ExportDefinition, ...]:
        """Get all private definitions (single underscore)."""
        return tuple(d for d in self.definitions if d.visibility == Visibility.PRIVATE)
    
    @property
    def callable_exports(self) -> Tuple[ExportDefinition, ...]:
        """Get all public callable exports."""
        return tuple(
            d for d in self.public_definitions 
            if d.definition_type in (DefinitionType.FUNCTION, DefinitionType.CLASS)
        )


class ExportSight(AbstractEye):
    """
    Observes what a module publicly exposes.
    
    Key principles:
    1. Only records what is textually declared
    2. Respects __all__ if present
    3. Uses naming conventions as fallback
    4. Never guesses intent
    """
    
    VERSION = "1.0.0"
    
    def __init__(self) -> None:
        super().__init__(name="export_sight", version=self.VERSION)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Explicitly declare capabilities."""
        return {
            "name": self.name,
            "version": self.version,
            "deterministic": True,
            "side_effect_free": True,
            "language": "python",
            "analysis_type": "static_signatures"
        }
    
    def observe(self, target: Path) -> ObservationResult:
        """Public API: Observe exports from a Python source file."""
        return self._observe_with_timing(target)
    
    def _observe_impl(self, target: Path) -> ObservationResult:
        """
        Observe exports from a Python source file.
        
        Args:
            target: Path to Python source file
            
        Returns:
            ObservationResult containing module exports
            
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
            
            # Parse and extract exports
            explicit_all, definitions, errors = self._extract_exports(target, content)
            
            observation = ModuleExports(
                module_path=target.resolve(),
                file_hash=file_hash,
                timestamp=timestamp,
                explicit_all=tuple(explicit_all),
                definitions=tuple(definitions),
                errors=tuple(errors)
            )
            
            # Calculate confidence based on error ratio
            confidence = 1.0 - (len(errors) / max(len(definitions), 1))
            
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=confidence,
                raw_payload=observation
            )
            
        except UnicodeDecodeError:
            # File is not valid UTF-8 text
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=0.0,
                raw_payload=ModuleExports(
                    module_path=target.resolve(),
                    file_hash="",
                    timestamp=timestamp,
                    explicit_all=(),
                    definitions=(),
                    errors=("File is not valid UTF-8 text",)
                )
            )
    
    def _compute_hash(self, content: str) -> str:
        """Compute deterministic hash of file content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _extract_exports(
        self, 
        module_path: Path, 
        content: str
    ) -> Tuple[List[str], List[ExportDefinition], List[str]]:
        """
        Extract export information from Python source.
        
        Returns:
            Tuple of (explicit_all, definitions, errors)
        """
        explicit_all: List[str] = []
        definitions: List[ExportDefinition] = []
        errors: List[str] = []
        
        try:
            tree = ast.parse(content, filename=str(module_path))
            
            # First pass: find __all__ and top-level definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Check for __all__ assignment
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            all_values = self._extract_all_values(node.value)
                            explicit_all.extend(all_values)
            
            # Second pass: collect all top-level definitions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    definition = self._extract_function_definition(node)
                    if definition:
                        definitions.append(definition)
                elif isinstance(node, ast.ClassDef):
                    definition = self._extract_class_definition(node)
                    if definition:
                        definitions.append(definition)
                elif isinstance(node, ast.Assign):
                    # Handle constant/variable assignments
                    defs = self._extract_assignment_definition(node)
                    definitions.extend(defs)
                elif isinstance(node, ast.Import):
                    # Import statements at module level
                    defs = self._extract_import_definition(node)
                    definitions.extend(defs)
                elif isinstance(node, ast.ImportFrom):
                    defs = self._extract_import_definition(node)
                    definitions.extend(defs)
            
            # Determine visibility for each definition
            for definition in definitions:
                # Check if in explicit __all__
                if definition.name in explicit_all:
                    definition.visibility = Visibility.PUBLIC
                else:
                    # Use naming convention
                    definition.visibility = self._determine_visibility(definition.name)
            
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
        
        return explicit_all, definitions, errors
    
    def _extract_all_values(self, node: ast.AST) -> List[str]:
        """Extract string values from __all__ assignment."""
        values: List[str] = []
        
        if isinstance(node, ast.List):
            for element in node.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    values.append(element.value)
        elif isinstance(node, ast.Tuple):
            for element in node.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    values.append(element.value)
        
        return values
    
    def _extract_function_definition(
        self, 
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Optional[ExportDefinition]:
        """Extract function definition information."""
        try:
            # Extract signature
            signature = self._extract_function_signature(node)
            
            # Determine if generator
            is_generator = self._is_generator_function(node)
            
            # Get decorators
            decorators = [
                self._format_decorator(d) for d in node.decorator_list
            ]
            
            # Update signature with decorators
            signature = FunctionSignature(
                name=signature.name,
                parameters=signature.parameters,
                returns=signature.returns,
                decorators=tuple(decorators),
                is_async=isinstance(node, ast.AsyncFunctionDef),
                is_generator=is_generator,
                source_line=node.lineno
            )
            
            return ExportDefinition(
                name=node.name,
                definition_type=DefinitionType.FUNCTION,
                visibility=Visibility.PUBLIC,  # Will be updated later
                signature=signature,
                source_line=node.lineno,
                source_column=node.col_offset
            )
            
        except Exception:
            return None
    
    def _extract_function_signature(self, node: ast.FunctionDef) -> FunctionSignature:
        """Extract function signature details."""
        parameters: List[ParameterInfo] = []
        
        # Process args
        args = node.args
        arg_count = len(args.args) + len(args.kwonlyargs)
        
        # Positional arguments
        for i, arg in enumerate(args.args):
            param = ParameterInfo(
                name=arg.arg,
                annotation=self._format_annotation(arg.annotation) if arg.annotation else None,
                default=self._format_default(args.defaults, i, len(args.args)) if args.defaults else None,
                kind="POSITIONAL_OR_KEYWORD"
            )
            parameters.append(param)
        
        # *args
        if args.vararg:
            param = ParameterInfo(
                name=args.vararg.arg,
                annotation=self._format_annotation(args.vararg.annotation) if args.vararg.annotation else None,
                kind="VAR_POSITIONAL"
            )
            parameters.append(param)
        
        # Keyword-only arguments
        for i, arg in enumerate(args.kwonlyargs):
            param = ParameterInfo(
                name=arg.arg,
                annotation=self._format_annotation(arg.annotation) if arg.annotation else None,
                default=self._format_default(args.kw_defaults, i, len(args.kwonlyargs)) if args.kw_defaults else None,
                kind="KEYWORD_ONLY"
            )
            parameters.append(param)
        
        # **kwargs
        if args.kwarg:
            param = ParameterInfo(
                name=args.kwarg.arg,
                annotation=self._format_annotation(args.kwarg.annotation) if args.kwarg.annotation else None,
                kind="VAR_KEYWORD"
            )
            parameters.append(param)
        
        # Return annotation
        returns = self._format_annotation(node.returns) if node.returns else None
        
        return FunctionSignature(
            name=node.name,
            parameters=tuple(parameters),
            returns=returns,
            decorators=tuple(),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_generator=False,
            source_line=node.lineno
        )
    
    def _extract_class_definition(self, node: ast.ClassDef) -> Optional[ExportDefinition]:
        """Extract class definition information."""
        try:
            # Extract class signature
            signature = self._extract_class_signature(node)
            
            # Get decorators
            decorators = [
                self._format_decorator(d) for d in node.decorator_list
            ]
            
            # Update signature
            signature = ClassSignature(
                name=signature.name,
                bases=signature.bases,
                methods=signature.methods,
                class_attributes=signature.class_attributes,
                decorators=tuple(decorators),
                source_line=node.lineno,
                is_abstract=signature.is_abstract
            )
            
            return ExportDefinition(
                name=node.name,
                definition_type=DefinitionType.CLASS,
                visibility=Visibility.PUBLIC,  # Will be updated later
                signature=signature,
                source_line=node.lineno,
                source_column=node.col_offset
            )
            
        except Exception:
            return None
    
    def _extract_class_signature(self, node: ast.ClassDef) -> ClassSignature:
        """Extract class signature and methods."""
        # Base classes
        bases = [self._format_base(b) for b in node.bases]
        
        # Collect methods and class attributes
        methods: List[MethodInfo] = []
        class_attrs: List[str] = []
        is_abstract = False
        
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._extract_method_info(child)
                if method:
                    methods.append(method)
                    if method.is_abstract:
                        is_abstract = True
            elif isinstance(child, ast.Assign):
                # Class-level assignments
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        class_attrs.append(target.id)
        
        return ClassSignature(
            name=node.name,
            bases=tuple(bases),
            methods=tuple(methods),
            class_attributes=tuple(class_attrs),
            decorators=tuple(),
            source_line=node.lineno,
            is_abstract=is_abstract
        )
    
    def _extract_method_info(
        self, 
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Optional[MethodInfo]:
        """Extract information about a class method."""
        try:
            signature = self._extract_function_signature(node)
            
            # Check decorators
            is_classmethod = False
            is_staticmethod = False
            is_property = False
            is_abstract = False
            
            for decorator in node.decorator_list:
                decorator_name = self._format_decorator(decorator)
                if decorator_name == "classmethod":
                    is_classmethod = True
                elif decorator_name == "staticmethod":
                    is_staticmethod = True
                elif decorator_name == "property":
                    is_property = True
                elif "abstract" in decorator_name.lower():
                    is_abstract = True
            
            # Determine visibility
            visibility = self._determine_visibility(node.name)
            
            return MethodInfo(
                name=node.name,
                signature=signature,
                visibility=visibility,
                is_classmethod=is_classmethod,
                is_staticmethod=is_staticmethod,
                is_property=is_property,
                is_abstract=is_abstract
            )
            
        except Exception:
            return None
    
    def _extract_assignment_definition(
        self, 
        node: ast.Assign
    ) -> List[ExportDefinition]:
        """Extract definitions from assignment statements."""
        definitions: List[ExportDefinition] = []
        
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Determine type based on naming convention
                if target.id.isupper():
                    def_type = DefinitionType.CONSTANT
                else:
                    def_type = DefinitionType.VARIABLE
                
                definition = ExportDefinition(
                    name=target.id,
                    definition_type=def_type,
                    visibility=Visibility.PUBLIC,  # Will be updated
                    signature=None,
                    source_line=node.lineno,
                    source_column=node.col_offset
                )
                definitions.append(definition)
        
        return definitions
    
    def _extract_import_definition(
        self, 
        node: Union[ast.Import, ast.ImportFrom]
    ) -> List[ExportDefinition]:
        """Extract definitions from import statements."""
        definitions: List[ExportDefinition] = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                definition = ExportDefinition(
                    name=alias.asname or alias.name,
                    definition_type=DefinitionType.IMPORT,
                    visibility=Visibility.PUBLIC,
                    signature=None,
                    source_line=node.lineno,
                    source_column=node.col_offset
                )
                definitions.append(definition)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                definition = ExportDefinition(
                    name=alias.asname or alias.name,
                    definition_type=DefinitionType.IMPORT,
                    visibility=Visibility.PUBLIC,
                    signature=None,
                    source_line=node.lineno,
                    source_column=node.col_offset
                )
                definitions.append(definition)
        
        return definitions
    
    def _determine_visibility(self, name: str) -> Visibility:
        """Determine visibility based on naming convention."""
        if name.startswith("__") and name.endswith("__"):
            return Visibility.MODULE_PRIVATE
        elif name.startswith("__"):
            return Visibility.PRIVATE
        elif name.startswith("_"):
            return Visibility.PROTECTED
        else:
            return Visibility.PUBLIC
    
    def _format_annotation(self, node: ast.AST) -> Optional[str]:
        """Format type annotation as string."""
        try:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
        except Exception:
            return None
    
    def _format_default(
        self, 
        defaults: List[ast.AST], 
        index: int, 
        total: int
    ) -> Optional[str]:
        """Format default value as string."""
        try:
            # Calculate which default corresponds to this parameter
            default_index = index - (total - len(defaults))
            if 0 <= default_index < len(defaults):
                default_node = defaults[default_index]
                return ast.unparse(default_node) if hasattr(ast, 'unparse') else str(default_node)
        except Exception:
            pass
        return None
    
    def _format_decorator(self, node: ast.AST) -> str:
        """Format decorator as string."""
        try:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
        except Exception:
            return "<decorator>"
    
    def _format_base(self, node: ast.AST) -> str:
        """Format base class as string."""
        try:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
        except Exception:
            return "<base>"
    
    def _is_generator_function(self, node: ast.FunctionDef) -> bool:
        """Check if function contains yield statements."""
        for child in ast.walk(node):
            if isinstance(child, ast.Yield) or isinstance(child, ast.YieldFrom):
                return True
        return False
    
    def validate(self) -> bool:
        """Validate that this eye follows observation purity rules."""
        # Check for prohibited imports
        prohibited_imports = {
            'inspect.geto' + 'source',  # Might execute code
            'ev' + 'al(', 'ex' + 'ec(', 'com' + 'pile(',
            'import' + 'lib.import_module'
        }
        
        # Check this file's source
        current_file = Path(__file__).resolve()
        with open(current_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for prohibited in prohibited_imports:
            if prohibited in content:
                return False
        
        # Ensure no execution-related code
        execution_patterns = {
            'ex' + 'ec(', 'ev' + 'al(', 'com' + 'pile(',
            'getat' + 'tr(', 'setat' + 'tr(',
            'sub' + 'process', 'os.sys' + 'tem',
            'open(' + '"w")', 'open(' + '"a")'
        }
        
        for pattern in execution_patterns:
            if pattern in content:
                return False
        
        return True


# Convenience functions

def observe_exports(file_path: Union[str, Path]) -> ModuleExports:
    """Convenience function for observing exports from a file."""
    sight = ExportSight()
    path = Path(file_path) if isinstance(file_path, str) else file_path
    result = sight.observe(path)
    return result.raw_payload



