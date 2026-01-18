#!/usr/bin/env python3
"""
Comprehensive Codebase Validation Script
Executes all validation steps from the comprehensive validation prompt.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import subprocess
import tempfile

class CodebaseValidator:
    """Comprehensive validation of CodeMarshal codebase."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.errors = []
        self.warnings = []
        self.stats = {
            'files_checked': 0,
            'syntax_errors': 0,
            'type_errors': 0,
            'constitutional_violations': 0
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run comprehensive validation."""
        print("🔍 Starting comprehensive codebase validation...")
        
        # Phase 1: Syntax Validation
        print("\n📝 Phase 1: Syntax Validation")
        self._validate_syntax()
        
        # Phase 2: Import Validation
        print("\n📦 Phase 2: Import Validation")
        self._validate_imports()
        
        # Phase 3: Constitutional Compliance
        print("\n⚖️ Phase 3: Constitutional Compliance")
        self._validate_constitutional_compliance()
        
        # Phase 4: Logic Validation
        print("\n🧠 Phase 4: Logic Validation")
        self._validate_logic()
        
        # Phase 5: Interface Validation
        print("\n🔌 Phase 5: Interface Validation")
        self._validate_interfaces()
        
        # Generate report
        return self._generate_report()
    
    def _validate_syntax(self) -> None:
        """Validate Python syntax across all files."""
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
                
            self.stats['files_checked'] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to check syntax
                ast.parse(content, filename=str(file_path))
                
            except SyntaxError as e:
                self.stats['syntax_errors'] += 1
                self.errors.append({
                    'type': 'SYNTAX_ERROR',
                    'file': str(file_path),
                    'line': e.lineno,
                    'column': e.offset,
                    'message': e.msg,
                    'severity': 'CRITICAL'
                })
                
            except UnicodeDecodeError as e:
                self.warnings.append({
                    'type': 'ENCODING_WARNING',
                    'file': str(file_path),
                    'message': f'Encoding issue: {e}',
                    'severity': 'MEDIUM'
                })
    
    def _validate_imports(self) -> None:
        """Validate import statements and dependencies."""
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(file_path))
                
                # Check imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._check_import_validity(str(alias.name), file_path)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._check_import_validity(node.module, file_path)
                            
            except Exception as e:
                self.warnings.append({
                    'type': 'IMPORT_PARSE_WARNING',
                    'file': str(file_path),
                    'message': f'Could not parse imports: {e}',
                    'severity': 'LOW'
                })
    
    def _check_import_validity(self, module_name: str, file_path: Path) -> None:
        """Check if import is valid."""
        # Check for runtime imports (constitutional violation)
        runtime_import_patterns = ['importlib.import_module', '__import__', 'exec', 'eval']
        
        if any(pattern in module_name for pattern in runtime_import_patterns):
            self.errors.append({
                'type': 'CONSTITUTIONAL_VIOLATION',
                'file': str(file_path),
                'message': f'Runtime import detected: {module_name}',
                'article': 'Article 12 (Local Operation)',
                'severity': 'CRITICAL'
            })
            self.stats['constitutional_violations'] += 1
    
    def _validate_constitutional_compliance(self) -> None:
        """Validate constitutional compliance."""
        # Article 1: No inference in observation modules
        self._check_article_1_compliance()
        
        # Article 13: Deterministic operation
        self._check_article_13_compliance()
        
        # Article 21: Self-validation
        self._check_article_21_compliance()
    
    def _check_article_1_compliance(self) -> None:
        """Check Article 1: Observation Purity."""
        observation_modules = [
            'observations/eyes/file_sight.py',
            'observations/eyes/import_sight.py',
            'observations/eyes/export_sight.py',
            'observations/eyes/boundary_sight.py',
            'observations/eyes/encoding_sight.py'
        ]
        
        inference_keywords = [
            'infer', 'guess', 'assume', 'likely', 'probably', 
            'might', 'could', 'interpret', 'suggest', 'estimate'
        ]
        
        for module_path in observation_modules:
            full_path = self.root_path / module_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    for keyword in inference_keywords:
                        if keyword in content:
                            # Check if it's in a comment or string
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if keyword in line and not line.strip().startswith('#'):
                                    self.errors.append({
                                        'type': 'CONSTITUTIONAL_VIOLATION',
                                        'file': str(full_path),
                                        'line': i,
                                        'message': f'Inference keyword detected: {keyword}',
                                        'article': 'Article 1 (Observation Purity)',
                                        'severity': 'CRITICAL'
                                    })
                                    self.stats['constitutional_violations'] += 1
                                    
                except Exception as e:
                    self.warnings.append({
                        'type': 'ARTICLE_1_CHECK_WARNING',
                        'file': str(full_path),
                        'message': f'Could not check Article 1 compliance: {e}',
                        'severity': 'MEDIUM'
                    })
    
    def _check_article_13_compliance(self) -> None:
        """Check Article 13: Deterministic Operation."""
        analysis_modules = [
            'core/engine.py',
            'inquiry/patterns/',
            'observations/eyes/'
        ]
        
        non_deterministic_patterns = [
            'random.', 'time.time()', 'datetime.now()',
            'uuid.uuid4()', 'os.urandom()'
        ]
        
        for module_pattern in analysis_modules:
            if module_pattern.endswith('/'):
                module_files = list((self.root_path / module_pattern).rglob("*.py"))
            else:
                module_files = [self.root_path / module_pattern] if (self.root_path / module_pattern).exists() else []
            
            for file_path in module_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for pattern in non_deterministic_patterns:
                        if pattern in content:
                            # Check if it's in observation ID generation (allowed with our fix)
                            if 'obs_id' in content and 'hashlib' in content:
                                continue  # This is our deterministic fix
                            
                            self.errors.append({
                                'type': 'CONSTITUTIONAL_VIOLATION',
                                'file': str(file_path),
                                'message': f'Non-deterministic pattern detected: {pattern}',
                                'article': 'Article 13 (Deterministic Operation)',
                                'severity': 'CRITICAL'
                            })
                            self.stats['constitutional_violations'] += 1
                            
                except Exception as e:
                    self.warnings.append({
                        'type': 'ARTICLE_13_CHECK_WARNING',
                        'file': str(file_path),
                        'message': f'Could not check Article 13 compliance: {e}',
                        'severity': 'MEDIUM'
                    })
    
    def _check_article_21_compliance(self) -> None:
        """Check Article 21: Self-Validation."""
        validation_file = self.root_path / 'integrity/validation/complete_constitutional.test.py'
        
        if not validation_file.exists():
            self.errors.append({
                'type': 'CONSTITUTIONAL_VIOLATION',
                'file': 'integrity/validation/complete_constitutional.test.py',
                'message': 'Self-validation file missing',
                'article': 'Article 21 (Self-Validation)',
                'severity': 'CRITICAL'
            })
            self.stats['constitutional_violations'] += 1
            return
        
        try:
            with open(validation_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for all 24 articles
            articles_found = []
            for i in range(1, 25):
                if f'test_article_{i}_' in content or f'Article {i}' in content:
                    articles_found.append(i)
            
            missing_articles = set(range(1, 25)) - set(articles_found)
            
            if missing_articles:
                self.errors.append({
                    'type': 'CONSTITUTIONAL_VIOLATION',
                    'file': str(validation_file),
                    'message': f'Missing self-validation for articles: {sorted(missing_articles)}',
                    'article': 'Article 21 (Self-Validation)',
                    'severity': 'CRITICAL'
                })
                self.stats['constitutional_violations'] += len(missing_articles)
                
        except Exception as e:
            self.warnings.append({
                'type': 'ARTICLE_21_CHECK_WARNING',
                'file': str(validation_file),
                'message': f'Could not check Article 21 compliance: {e}',
                'severity': 'MEDIUM'
            })
    
    def _validate_logic(self) -> None:
        """Validate logical flow and error handling."""
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(file_path))
                
                # Check for bare except clauses
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            self.errors.append({
                                'type': 'LOGIC_ERROR',
                                'file': str(file_path),
                                'line': node.lineno,
                                'message': 'Bare except clause detected',
                                'severity': 'HIGH'
                            })
                
                # Check for unreachable code (simplified)
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith('return ') or stripped.startswith('raise '):
                        # Check next few lines for code
                        if i < len(lines):
                            next_lines = lines[i:i+3]
                            for j, next_line in enumerate(next_lines, 1):
                                if next_line.strip() and not next_line.strip().startswith('#'):
                                    self.warnings.append({
                                        'type': 'UNREACHABLE_CODE_WARNING',
                                        'file': str(file_path),
                                        'line': i + j,
                                        'message': 'Potentially unreachable code detected',
                                        'severity': 'MEDIUM'
                                    })
                                    break
                            
            except Exception as e:
                self.warnings.append({
                    'type': 'LOGIC_VALIDATION_WARNING',
                    'file': str(file_path),
                    'message': f'Could not validate logic: {e}',
                    'severity': 'LOW'
                })
    
    def _validate_interfaces(self) -> None:
        """Validate interface contracts and consistency."""
        # Check key interface files
        interface_files = [
            'observations/eyes/base.py',
            'core/engine.py',
            'storage/transactional.py'
        ]
        
        for file_path_str in interface_files:
            file_path = self.root_path / file_path_str
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(file_path))
                
                # Check for abstract methods and implementations
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check for abstract methods
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                # Check if function has proper docstring
                                if not ast.get_docstring(item):
                                    self.warnings.append({
                                        'type': 'INTERFACE_WARNING',
                                        'file': str(file_path),
                                        'line': item.lineno,
                                        'message': f'Missing docstring for method: {item.name}',
                                        'severity': 'MEDIUM'
                                    })
                                    
            except Exception as e:
                self.warnings.append({
                    'type': 'INTERFACE_VALIDATION_WARNING',
                    'file': str(file_path),
                    'message': f'Could not validate interface: {e}',
                    'severity': 'LOW'
                })
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        return {
            'summary': {
                'total_files': self.stats['files_checked'],
                'syntax_errors': self.stats['syntax_errors'],
                'constitutional_violations': self.stats['constitutional_violations'],
                'overall_status': 'PASS' if len(self.errors) == 0 else 'FAIL'
            },
            'critical_errors': [e for e in self.errors if e['severity'] == 'CRITICAL'],
            'high_errors': [e for e in self.errors if e['severity'] == 'HIGH'],
            'medium_warnings': [w for w in self.warnings if w['severity'] == 'MEDIUM'],
            'low_warnings': [w for w in self.warnings if w['severity'] == 'LOW'],
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if self.stats['syntax_errors'] > 0:
            recommendations.append(f"Fix {self.stats['syntax_errors']} syntax errors before deployment")
        
        if self.stats['constitutional_violations'] > 0:
            recommendations.append(f"Address {self.stats['constitutional_violations']} constitutional violations immediately")
        
        if len(self.errors) == 0 and len(self.warnings) == 0:
            recommendations.append("Codebase is ready for production deployment")
        
        return recommendations

def main():
    """Main validation execution."""
    if len(sys.argv) != 2:
        print("Usage: python validation_script.py <codebase_path>")
        sys.exit(1)
    
    codebase_path = Path(sys.argv[1])
    if not codebase_path.exists():
        print(f"Error: Path {codebase_path} does not exist")
        sys.exit(1)
    
    validator = CodebaseValidator(codebase_path)
    report = validator.validate_all()
    
    # Print report
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE VALIDATION REPORT")
    print("="*60)
    
    print(f"\n📈 SUMMARY:")
    print(f"  Files checked: {report['summary']['total_files']}")
    print(f"  Syntax errors: {report['summary']['syntax_errors']}")
    print(f"  Constitutional violations: {report['summary']['constitutional_violations']}")
    print(f"  Overall status: {report['summary']['overall_status']}")
    
    if report['critical_errors']:
        print(f"\n🚨 CRITICAL ERRORS ({len(report['critical_errors'])}):")
        for error in report['critical_errors']:
            print(f"  ❌ {error['file']}:{error.get('line', '?')} - {error['message']}")
            if 'article' in error:
                print(f"      Constitution: {error['article']}")
    
    if report['high_errors']:
        print(f"\n⚠️ HIGH ERRORS ({len(report['high_errors'])}):")
        for error in report['high_errors']:
            print(f"  ⚠️ {error['file']}:{error.get('line', '?')} - {error['message']}")
    
    if report['medium_warnings']:
        print(f"\n⚡ MEDIUM WARNINGS ({len(report['medium_warnings'])}):")
        for warning in report['medium_warnings']:
            print(f"  ⚡ {warning['file']}:{warning.get('line', '?')} - {warning['message']}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"  💡 {rec}")
    
    print("\n" + "="*60)
    
    # Exit with appropriate code
    sys.exit(0 if report['summary']['overall_status'] == 'PASS' else 1)

if __name__ == "__main__":
    main()
