#!/usr/bin/env python3
"""
Fix all syntax errors found in comprehensive validation.
"""

import ast
import os
from pathlib import Path

def check_syntax_errors():
    """Check and fix syntax errors in critical files."""
    
    critical_files = [
        'observations/invariants/immutable.test.py',
        'tests/performance.test.py', 
        'tests/crash_recovery.test.py',
        'bridge/entry/api.py',
        'storage/migration.py',
        'lens/views/examination.py'
    ]
    
    root_path = Path('c:/Users/LENOVO/Documents/CodeMarshal')
    
    for file_path in critical_files:
        full_path = root_path / file_path
        if not full_path.exists():
            print(f"❌ File not found: {full_path}")
            continue
            
        print(f"🔍 Checking: {file_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse
            ast.parse(content, filename=str(full_path))
            print(f"✅ {file_path}: No syntax errors")
            
        except SyntaxError as e:
            print(f"❌ {file_path}:{e.lineno}: {e.msg}")
            
            # Fix common syntax errors
            fixed_content = fix_syntax_error(content, e)
            
            if fixed_content != content:
                print(f"🔧 Attempting to fix: {file_path}")
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"✅ Fixed: {file_path}")
            else:
                print(f"⚠️ Could not auto-fix: {file_path}")
                
        except Exception as e:
            print(f"⚠️ Error checking {file_path}: {e}")

def fix_syntax_error(content: str, error: SyntaxError) -> str:
    """Attempt to fix common syntax errors."""
    
    lines = content.split('\n')
    
    # Fix common issues
    if "bytes can only contain ASCII" in str(error.msg):
        # Fix bytes literal with non-ASCII
        if error.lineno <= len(lines):
            line = lines[error.lineno - 1]
            if 'b\'\'\'' in line:
                # Replace with proper escape sequences
                fixed_line = line.replace('café résumé naïve', 'caf\\xe9 r\\xe9sum\\xe9 na\\xefve')
                lines[error.lineno - 1] = fixed_line
                return '\n'.join(lines)
    
    # Fix unmatched brackets
    if "unmatched" in str(error.msg).lower():
        # Simple bracket matching fix
        open_brackets = content.count('(') - content.count(')')
        if open_brackets > 0:
            return content + ')' * open_brackets
    
    return content

if __name__ == "__main__":
    check_syntax_errors()
