"""
Network Access Prohibition Enforcement
======================================

Enforces local-only operation in truth-critical modules (core/, observations/, inquiry/, lens/).
Prevents network calls that violate local operation requirement (Tier 12).

Violations are logged to integrity/monitoring/errors.py and reported as structured violations.
"""

import builtins
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Type
from types import ModuleType

# Import for monitoring integration
from integrity.monitoring.errors import log_integrity_violation


class NetworkAccessViolation(Exception):
    """Raised when network access is detected in truth-critical code."""
    
    def __init__(self, violation_data: Dict[str, str]) -> None:
        self.violation_data = violation_data
        super().__init__(f"Network access violation: {violation_data}")


class NetworkModuleDetector:
    """
    Detects network-related modules loaded in the system.
    
    Uses textual analysis of module names and known network libraries.
    Strictly follows truth-preserving principles: only detects what is present.
    """
    
    # Comprehensive list of known network-related module names
    NETWORK_MODULES: List[str] = [
        # Standard library network modules
        'socket', 'ssl', 'http', 'urllib', 'ftplib', 'poplib', 'imaplib', 'smtplib',
        'telnetlib', 'xmlrpc', 'webbrowser', 'asyncio.streams', 'asyncio.protocols',
        'selectors', 'select', 'subprocess',  # subprocess can create network processes
        'ipaddress', 'email', 'mailbox', 'mimetypes',  # email/network related
        
        # Common third-party network libraries
        'requests', 'aiohttp', 'httpx', 'tornado', 'twisted', 'websockets', 'websocket',
        'paramiko', 'boto', 'boto3', 'botocore', 'azure', 'google.cloud',
        'grpc', 'zmq', 'pika', 'kombu', 'redis', 'pymongo', 'psycopg2', 'mysql',
        'sqlite3',  # Database access considered network-like for truth-critical code
        
        # Testing frameworks with network capabilities
        'unittest.mock.patch', 'unittest.mock.Mock',  # Can mock network calls
        
        # Async frameworks with network capabilities
        'trio', 'curio', 'anyio',
        
        # System modules that can perform network operations
        'os.system', 'os.popen', 'os.spawn', 'os.exec',
        'shutil.copyfileobj',  # Can copy from network paths
    ]
    
    # Network-related function patterns in standard library
    NETWORK_FUNCTIONS: List[str] = [
        'open',  # Could open network URLs with certain handlers
        'urlopen', 'urlretrieve', 'urlparse', 'urljoin',
        'connect', 'bind', 'listen', 'accept', 'send', 'recv',
        'request', 'get', 'post', 'put', 'delete',
        'download', 'upload', 'fetch', 'query',
        'publish', 'subscribe', 'broadcast',
        'execute', 'call', 'invoke',  # Could be RPC
    ]
    
    def __init__(self) -> None:
        self.violations: List[Dict[str, str]] = []
        
    def check_loaded_modules(self) -> List[Dict[str, str]]:
        """
        Check all currently loaded modules for network-related imports.
        
        Returns:
            List of violation dictionaries.
        """
        violations: List[Dict[str, str]] = []
        
        for module_name, module in sys.modules.items():
            # Only check truth-critical modules
            if not self._is_truth_critical_module(module_name):
                continue
                
            # Check if module imports any known network modules
            module_violations = self._check_module_for_network_imports(module, module_name)
            violations.extend(module_violations)
            
        return violations
        
    def _is_truth_critical_module(self, module_name: str) -> bool:
        """Check if a module is in a truth-critical package."""
        return any(module_name.startswith(prefix) for prefix in 
                  ('core.', 'observations.', 'inquiry.', 'lens.'))
        
    def _check_module_for_network_imports(self, module: ModuleType, module_name: str) -> List[Dict[str, str]]:
        """
        Check a single module for network-related imports.
        
        Args:
            module: The module object to check.
            module_name: Name of the module.
            
        Returns:
            List of violation dictionaries.
        """
        violations: List[Dict[str, str]] = []
        
        try:
            # Get module's __dict__ to see imported names
            module_dict = module.__dict__
            
            for attr_name, attr_value in module_dict.items():
                # Check if attribute is a module
                if isinstance(attr_value, ModuleType):
                    attr_module_name = getattr(attr_value, '__name__', str(attr_value))
                    
                    # Check if this module is network-related
                    if self._is_network_module(attr_module_name):
                        violations.append({
                            "violation": "network_access",
                            "module": module_name,
                            "imported_module": attr_module_name,
                            "details": f"Imported network module '{attr_module_name}' as '{attr_name}'",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
        except (AttributeError, TypeError, KeyError):
            # Module may be a built-in or have restricted __dict__
            pass
            
        return violations
        
    def _is_network_module(self, module_name: str) -> bool:
        """
        Check if a module name indicates network functionality.
        
        Args:
            module_name: Name of the module to check.
            
        Returns:
            True if module is network-related, False otherwise.
        """
        # Normalize module name
        module_name_lower = module_name.lower()
        
        # Check against known network modules
        for network_module in self.NETWORK_MODULES:
            if (network_module in module_name_lower or 
                module_name_lower.startswith(network_module + '.')):
                return True
                
        # Check for common network-related prefixes
        network_prefixes = ['http', 'ftp', 'smtp', 'pop', 'imap', 'telnet', 'ssh', 
                           'websocket', 'socket', 'ssl', 'tls']
        for prefix in network_prefixes:
            if module_name_lower.startswith(prefix):
                return True
                
        return False
        
    def _is_network_function(self, func_name: str) -> bool:
        """
        Check if a function name indicates network functionality.
        
        Args:
            func_name: Name of the function to check.
            
        Returns:
            True if function name suggests network operations.
        """
        func_lower = func_name.lower()
        
        for network_func in self.NETWORK_FUNCTIONS:
            if network_func in func_lower:
                return True
                
        return False


class NetworkAccessGuard:
    """
    Guards against network access by patching network-related modules.
    
    This is a runtime guard that intercepts network calls and raises exceptions.
    Should only be used in test environments or as a safety net.
    """
    
    def __init__(self) -> None:
        self._original_modules: Dict[str, Optional[ModuleType]] = {}
        self._original_functions: Dict[str, Optional[Callable]] = {}
        self._patched_modules: List[str] = []
        
    def install_guard(self) -> None:
        """Install network access guard by patching network modules."""
        self._patch_socket_module()
        self._patch_http_modules()
        self._patch_urllib_modules()
        self._patch_requests_module()
        self._patch_os_system_calls()
        
    def remove_guard(self) -> None:
        """Remove all network access guards."""
        for module_name, original_module in self._original_modules.items():
            if original_module is not None:
                sys.modules[module_name] = original_module
                
        for func_name, original_func in self._original_functions.items():
            if original_func is not None:
                # Restore built-in functions
                if hasattr(builtins, func_name):
                    setattr(builtins, func_name, original_func)
                    
        self._original_modules.clear()
        self._original_functions.clear()
        self._patched_modules.clear()
        
    def _patch_socket_module(self) -> None:
        """Patch the socket module to prevent network access."""
        try:
            import socket as original_socket
            
            # Create a guarded socket module
            class GuardedSocket:
                def __getattr__(self, name: str) -> Any:
                    raise NetworkAccessViolation({
                        "violation": "network_access",
                        "module": "socket",
                        "details": f"Access to socket.{name} blocked",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
            # Replace socket module
            self._original_modules['socket'] = original_socket
            sys.modules['socket'] = GuardedSocket()
            self._patched_modules.append('socket')
            
        except ImportError:
            pass
            
    def _patch_http_modules(self) -> None:
        """Patch HTTP-related modules."""
        http_modules = ['http.client', 'http.server', 'httplib']
        
        for module_name in http_modules:
            try:
                original_module = __import__(module_name)
                
                class GuardedHTTPModule:
                    def __getattr__(self, name: str) -> Any:
                        raise NetworkAccessViolation({
                            "violation": "network_access",
                            "module": module_name,
                            "details": f"Access to {module_name}.{name} blocked",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                self._original_modules[module_name] = original_module
                sys.modules[module_name] = GuardedHTTPModule()
                self._patched_modules.append(module_name)
                
            except ImportError:
                continue
                
    def _patch_urllib_modules(self) -> None:
        """Patch urllib modules."""
        urllib_modules = ['urllib.request', 'urllib.response', 'urllib.parse', 
                         'urllib.error', 'urllib.robotparser']
        
        for module_name in urllib_modules:
            try:
                original_module = __import__(module_name)
                
                class GuardedURLLibModule:
                    def __getattr__(self, name: str) -> Any:
                        raise NetworkAccessViolation({
                            "violation": "network_access",
                            "module": module_name,
                            "details": f"Access to {module_name}.{name} blocked",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                self._original_modules[module_name] = original_module
                sys.modules[module_name] = GuardedURLLibModule()
                self._patched_modules.append(module_name)
                
            except ImportError:
                continue
                
    def _patch_requests_module(self) -> None:
        """Patch the requests module if installed."""
        try:
            import requests as original_requests
            
            class GuardedRequests:
                def __getattr__(self, name: str) -> Any:
                    raise NetworkAccessViolation({
                        "violation": "network_access",
                        "module": "requests",
                        "details": f"Access to requests.{name} blocked",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
            self._original_modules['requests'] = original_requests
            sys.modules['requests'] = GuardedRequests()
            self._patched_modules.append('requests')
            
        except ImportError:
            pass
            
    def _patch_os_system_calls(self) -> None:
        """Patch os.system and related calls to prevent network execution."""
        import os
        
        # Patch os.system
        if hasattr(os, 'system'):
            original_system = os.system
            
            def guarded_system(command: str) -> int:
                # Check if command contains network-related operations
                command_lower = command.lower()
                network_keywords = ['curl', 'wget', 'ssh', 'scp', 'ftp', 'telnet',
                                   'ping', 'traceroute', 'netcat', 'nc', 'nmap']
                
                for keyword in network_keywords:
                    if keyword in command_lower:
                        raise NetworkAccessViolation({
                            "violation": "network_access",
                            "module": "os",
                            "details": f"Network command '{keyword}' in os.system call",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                # Allow non-network commands
                return original_system(command)
                
            os.system = guarded_system
            self._original_functions['os.system'] = original_system
            
        # Patch os.popen
        if hasattr(os, 'popen'):
            original_popen = os.popen
            
            def guarded_popen(command: str, *args: Any, **kwargs: Any) -> Any:
                # Similar check for network commands
                command_lower = command.lower()
                network_keywords = ['curl', 'wget', 'ssh', 'scp', 'ftp']
                
                for keyword in network_keywords:
                    if keyword in command_lower:
                        raise NetworkAccessViolation({
                            "violation": "network_access",
                            "module": "os",
                            "details": f"Network command '{keyword}' in os.popen call",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                return original_popen(command, *args, **kwargs)
                
            os.popen = guarded_popen
            self._original_functions['os.popen'] = original_popen


def enforce_no_network() -> List[Dict[str, str]]:
    """
    Enforce prohibition on network access in truth-critical modules.
    
    Returns:
        List of violation dictionaries with keys:
        - violation: Always "network_access"
        - module: Module name where violation occurred
        - imported_module: Network module that was imported (if applicable)
        - details: Human-readable details
        - timestamp: ISO timestamp of detection
    """
    violations: List[Dict[str, str]] = []
    
    # Use detector to find network module imports
    detector = NetworkModuleDetector()
    import_violations = detector.check_loaded_modules()
    
    # Log each violation
    for violation in import_violations:
        log_integrity_violation(
            violation_type="network_access",
            location={
                "module": violation["module"],
                "imported_module": violation.get("imported_module")
            },
            details=violation["details"],
            severity="critical"
        )
        
    violations.extend(import_violations)
    
    # Check for network function usage in truth-critical code
    # This is more invasive and optional
    function_violations = _check_for_network_function_calls()
    violations.extend(function_violations)
    
    return violations


def _check_for_network_function_calls() -> List[Dict[str, str]]:
    """
    Check for calls to known network functions in truth-critical modules.
    
    This is a more invasive check that requires examining call sites.
    Returns empty list by default; implement if needed.
    """
    # For now, return empty list - this is an advanced check
    # that could be implemented with AST analysis similar to no_runtime_imports
    return []


def validate_no_network_access() -> bool:
    """
    Validate that no network access is present in truth-critical modules.
    
    Returns:
        True if no network access detected, False otherwise.
        
    Raises:
        NetworkAccessViolation: If network access is detected (for test mode).
    """
    violations = enforce_no_network()
    
    if violations:
        # For test mode, raise exception with first violation
        raise NetworkAccessViolation(violations[0])
        
    return len(violations) == 0


def install_network_guard() -> NetworkAccessGuard:
    """
    Install runtime network access guard.
    
    Returns:
        NetworkAccessGuard instance that can be used to remove guard later.
        
    WARNING: This is invasive and should only be used in test environments.
    """
    guard = NetworkAccessGuard()
    guard.install_guard()
    return guard


# Test function for module verification
def test_no_network() -> Dict[str, Any]:
    """
    Test function to verify the prohibition works.
    
    Returns:
        Dictionary with test results.
    """
    results = {
        "module": __name__,
        "function": "test_no_network",
        "status": "running",
        "violations_found": 0,
        "violations": []
    }
    
    try:
        violations = enforce_no_network()
        results["violations_found"] = len(violations)
        results["violations"] = violations
        results["status"] = "passed" if len(violations) == 0 else "failed"
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        
    return results


if __name__ == "__main__":
    # Command-line interface for standalone testing
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check truth-critical modules for network access."
    )
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Run test and exit with code 0 (no violations) or 1 (violations found)"
    )
    parser.add_argument(
        "--install-guard",
        action="store_true",
        help="Install network guard to block network calls (invasive, test-only)"
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="List all network-related modules currently imported"
    )
    
    args = parser.parse_args()
    
    if args.install_guard:
        guard = install_network_guard()
        print(f"Network guard installed. {len(guard._patched_modules)} modules patched.")
        if guard._patched_modules:
            print(f"Patched modules: {', '.join(guard._patched_modules)}")
            
    if args.list_modules:
        detector = NetworkModuleDetector()
        all_modules = list(sys.modules.keys())
        network_modules = [m for m in all_modules if detector._is_network_module(m)]
        
        print(f"Found {len(network_modules)} network-related modules in sys.modules:")
        for module in sorted(network_modules):
            print(f"  - {module}")
            
    if args.test:
        violations = enforce_no_network()
        if violations:
            print(f"FAILED: {len(violations)} network access violations found:")
            for v in violations[:5]:  # Show first 5
                print(f"  - {v['module']}: {v.get('imported_module', 'N/A')}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
            sys.exit(1)
        else:
            print("PASSED: No network access violations found.")
            sys.exit(0)
    else:
        # Default: just check and report
        violations = enforce_no_network()
        if violations:
            print(f"Network access violations found: {len(violations)}")
            for v in violations:
                print(f"\nModule: {v['module']}")
                if 'imported_module' in v:
                    print(f"Imported: {v['imported_module']}")
                print(f"Details: {v['details']}")
        else:
            print("No network access violations detected.")