#!/usr/bin/env python3
"""
Development Environment Verification Script
Verifies that all components of the development environment are properly configured
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

import httpx
import psutil

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, color: str = Colors.BLUE):
    """Print status message with color"""
    print(f"{color}[VERIFY]{Colors.END} {message}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {message}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")

def check_command_exists(command: str, name: str) -> bool:
    """Check if a command exists in PATH"""
    try:
        result = subprocess.run(['which', command], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"{name} is installed at {result.stdout.strip()}")
            return True
        else:
            print_error(f"{name} is not installed")
            return False
    except Exception as e:
        print_error(f"Error checking {name}: {e}")
        return False

def check_python_version() -> bool:
    """Check Python version (requires 3.11+)"""
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        version_str = result.stdout.strip()
        version = tuple(map(int, version_str.split()[1].split('.')[:2]))

        if version >= (3, 11):
            print_success(f"Python {version_str} is installed (>= 3.11)")
            return True
        else:
            print_error(f"Python {version_str} is installed but >= 3.11 is required")
            return False
    except Exception as e:
        print_error(f"Error checking Python version: {e}")
        return False

def check_node_version() -> bool:
    """Check Node.js version (requires 18+)"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version_str = result.stdout.strip()
        version = tuple(map(int, version_str[1:].split('.')[:2]))

        if version >= (18, 0):
            print_success(f"Node.js {version_str} is installed (>= 18)")
            return True
        else:
            print_error(f"Node.js {version_str} is installed but >= 18 is required")
            return False
    except Exception as e:
        print_error(f"Error checking Node.js version: {e}")
        return False

def check_docker_running() -> bool:
    """Check if Docker is running"""
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Docker is running")
            return True
        else:
            print_error("Docker is installed but not running")
            return False
    except Exception as e:
        print_error(f"Error checking Docker: {e}")
        return False

def check_docker_services() -> Dict[str, bool]:
    """Check if required Docker services are running"""
    services = {}

    try:
        # Check docker-compose.yml exists
        if not Path('docker-compose.yml').exists():
            print_error("docker-compose.yml not found")
            return services

        # Get running services
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'postgres' in line and 'Up' in line:
                    services['postgres'] = True
                    print_success("PostgreSQL is running")
                elif 'redis' in line and 'Up' in line:
                    services['redis'] = True
                    print_success("Redis is running")
        else:
            print_error("Error checking Docker services")

        # Check for missing services
        if 'postgres' not in services:
            print_warning("PostgreSQL is not running")
            services['postgres'] = False
        if 'redis' not in services:
            print_warning("Redis is not running")
            services['redis'] = False

    except Exception as e:
        print_error(f"Error checking Docker services: {e}")

    return services

def check_environment_files() -> Dict[str, bool]:
    """Check if environment files exist and have required variables"""
    env_files = {
        'services/orchestrator/.env': [],
        'services/console/.env': [],
        'services/terminal-daemon/.env': []
    }

    required_vars = {
        'services/orchestrator/.env': ['SECRET_KEY', 'JWT_SECRET', 'DATABASE_URL'],
        'services/console/.env': ['NEXTAUTH_SECRET', 'NEXTAUTH_URL'],
        'services/terminal-daemon/.env': ['PORT', 'KYROS_DAEMON_PORT']
    }

    results = {}

    for env_file, required in required_vars.items():
        if Path(env_file).exists():
            print_success(f"{env_file} exists")

            # Check required variables
            missing_vars = []
            if Path(env_file).stat().st_size > 0:
                with open(env_file, 'r') as f:
                    content = f.read()
                    for var in required:
                        if f"{var}=" not in content or content.split(f"{var}=")[1].split('\n')[0] in ['', 'your_', 'default_']:
                            missing_vars.append(var)
            else:
                missing_vars = required

            if missing_vars:
                print_warning(f"{env_file} is missing variables: {', '.join(missing_vars)}")
                results[env_file] = False
            else:
                print_success(f"{env_file} has all required variables")
                results[env_file] = True
        else:
            print_error(f"{env_file} does not exist")
            results[env_file] = False

    return results

def check_python_dependencies() -> bool:
    """Check if Python dependencies are installed"""
    requirements_file = 'services/orchestrator/requirements.txt'

    if not Path(requirements_file).exists():
        print_error(f"{requirements_file} not found")
        return False

    try:
        # Check some key packages
        result = subprocess.run([
            sys.executable, '-c',
            'import fastapi, uvicorn, sqlalchemy, redis, httpx; print("Dependencies OK")'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print_success("Python dependencies are installed")
            return True
        else:
            print_error("Python dependencies are missing or corrupted")
            print_error(result.stderr)
            return False
    except Exception as e:
        print_error(f"Error checking Python dependencies: {e}")
        return False

def check_node_dependencies() -> Dict[str, bool]:
    """Check if Node.js dependencies are installed"""
    services = ['console', 'terminal-daemon']
    results = {}

    for service in services:
        package_json = f'services/{service}/package.json'
        node_modules = f'services/{service}/node_modules'

        if Path(package_json).exists():
            if Path(node_modules).exists() and Path(node_modules).is_dir():
                print_success(f"{service} Node dependencies are installed")
                results[service] = True
            else:
                print_warning(f"{service} package.json exists but node_modules is missing")
                results[service] = False
        else:
            print_error(f"{service} package.json not found")
            results[service] = False

    return results

async def check_orchestrator_api() -> bool:
    """Check if the orchestrator API is responding"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get('http://localhost:8000/healthz')
            if response.status_code == 200:
                print_success("Orchestrator API is responding")
                return True
            else:
                print_warning(f"Orchestrator API returned status {response.status_code}")
                return False
    except Exception as e:
        print_warning(f"Orchestrator API is not responding: {e}")
        return False

def check_collaboration_files() -> bool:
    """Check if collaboration state files exist"""
    state_dir = Path('collaboration/state')
    events_file = Path('collaboration/events/events.jsonl')

    success = True

    if state_dir.exists() and (state_dir / 'tasks.json').exists():
        print_success("Collaboration state files exist")
    else:
        print_warning("Collaboration state files missing")
        success = False

    if events_file.exists():
        print_success("Events file exists")
    else:
        print_warning("Events file missing")
        success = False

    return success

def check_mcp_config() -> bool:
    """Check if MCP configuration exists"""
    mcp_files = ['mcp.json', 'mcp.example.json']

    for mcp_file in mcp_files:
        if Path(mcp_file).exists():
            print_success(f"{mcp_file} exists")
            return True

    print_warning("No MCP configuration file found")
    return False

def check_port_availability() -> Dict[str, bool]:
    """Check if required ports are available"""
    required_ports = {
        3000: "Console frontend",
        3001: "Console alternative",
        8000: "Orchestrator API",
        8787: "Terminal daemon",
        6379: "Redis",
        5432: "PostgreSQL"
    }

    results = {}

    for port, service in required_ports.items():
        # Check if port is in use
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                print_warning(f"Port {port} ({service}) is in use by {conn.pid}")
                results[port] = False
                break
        else:
            print_success(f"Port {port} ({service}) is available")
            results[port] = True

    return results

async def run_health_checks() -> Dict[str, bool]:
    """Run comprehensive health checks"""
    print_status("Running comprehensive health checks...")

    results = {}

    # System requirements
    print_status("\n1. Checking System Requirements")
    results['docker'] = check_command_exists('docker', 'Docker')
    results['docker_compose'] = check_command_exists('docker-compose', 'Docker Compose')
    results['python'] = check_python_version()
    results['node'] = check_node_version()
    results['git'] = check_command_exists('git', 'Git')
    results['uv'] = check_command_exists('uv', 'UV (Python package manager)')
    results['npx'] = check_command_exists('npx', 'NPX (Node package runner)')

    # Docker services
    print_status("\n2. Checking Docker Services")
    if results['docker'] and check_docker_running():
        docker_services = check_docker_services()
        results.update(docker_services)

    # Environment configuration
    print_status("\n3. Checking Environment Configuration")
    env_files = check_environment_files()
    results.update({f'env_{k}': v for k, v in env_files.items()})

    # Dependencies
    print_status("\n4. Checking Dependencies")
    results['python_deps'] = check_python_dependencies()
    node_deps = check_node_dependencies()
    results.update({f'node_deps_{k}': v for k, v in node_deps.items()})

    # Application files
    print_status("\n5. Checking Application Files")
    results['collaboration_files'] = check_collaboration_files()
    results['mcp_config'] = check_mcp_config()

    # Port availability
    print_status("\n6. Checking Port Availability")
    ports = check_port_availability()
    results.update({f'port_{k}': v for k, v in ports.items()})

    # API health
    print_status("\n7. Checking API Health")
    results['orchestrator_api'] = await check_orchestrator_api()

    return results

def generate_report(results: Dict[str, bool]):
    """Generate a verification report"""
    print_status("\n" + "="*60)
    print_status("VERIFICATION REPORT")
    print_status("="*60)

    # Count successes and failures
    total = len(results)
    successes = sum(1 for v in results.values() if v)
    failures = total - successes

    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    print(f"Total checks: {total}")
    print(f"{Colors.GREEN}Passed: {successes}{Colors.END}")
    print(f"{Colors.RED}Failed: {failures}{Colors.END}")

    if failures == 0:
        print_success("\n🎉 All checks passed! Your development environment is ready.")
    else:
        print_warning(f"\n⚠️  {failures} check(s) failed. Please fix the issues above.")

        # Group failures by category
        print_status("\nFailed checks by category:")
        categories = {
            'System': ['docker', 'docker_compose', 'python', 'node', 'git', 'uv', 'npx'],
            'Services': ['postgres', 'redis', 'orchestrator_api'],
            'Configuration': ['env_services/orchestrator/.env', 'env_services/console/.env', 'env_services/terminal-daemon/.env'],
            'Dependencies': ['python_deps', 'node_deps_console', 'node_deps_terminal-daemon'],
            'Application': ['collaboration_files', 'mcp_config'],
            'Network': ['port_3000', 'port_3001', 'port_8000', 'port_8787', 'port_6379', 'port_5432']
        }

        for category, keys in categories.items():
            failed_in_category = [k for k in keys if k in results and not results[k]]
            if failed_in_category:
                print(f"  {category}: {', '.join(failed_in_category)}")

    # Save report to file
    report_file = 'verification-report.json'
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'results': results,
            'summary': {
                'total': total,
                'successes': successes,
                'failures': failures
            }
        }, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")

async def main():
    """Main verification function"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("==========================================")
    print("Kyros Praxis Development Environment Verification")
    print("==========================================")
    print(f"{Colors.END}")

    # Run all checks
    results = await run_health_checks()

    # Generate report
    generate_report(results)

    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    asyncio.run(main())