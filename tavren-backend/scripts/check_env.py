#!/usr/bin/env python3
"""
Development Environment Checker for Tavren

This script validates that the development environment is properly set up:
1. Correct Python version
2. Virtual environment activated
3. Required packages installed
4. Environment variables set correctly

Usage:
    python check_env.py [--skip-packages] [--verbose]
"""

import os
import sys
import subprocess
import argparse
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Define colors for terminal output
RESET = "\033[0m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"

# Required Python version
MIN_PYTHON_VERSION = (3, 8, 0)
RECOMMENDED_PYTHON_VERSION = (3, 9, 0)

# Path to requirements file
REQUIREMENTS_FILE = Path(__file__).parent.parent / "requirements.txt"

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{title.center(60)}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    print_header("Python Version Check")
    
    current_version = sys.version_info[:3]
    version_str = '.'.join(map(str, current_version))
    min_version_str = '.'.join(map(str, MIN_PYTHON_VERSION))
    recommended_version_str = '.'.join(map(str, RECOMMENDED_PYTHON_VERSION))
    
    print(f"Current Python version: {version_str}")
    print(f"Minimum required: {min_version_str}")
    print(f"Recommended: {recommended_version_str}")
    
    if current_version < MIN_PYTHON_VERSION:
        print(f"{RED}ERROR: Python version is below minimum requirement{RESET}")
        print(f"Please upgrade to at least Python {min_version_str}")
        return False
    elif current_version < RECOMMENDED_PYTHON_VERSION:
        print(f"{YELLOW}WARNING: Python version meets minimum but is below recommended version{RESET}")
        print(f"Consider upgrading to Python {recommended_version_str} for best compatibility")
        return True
    else:
        print(f"{GREEN}SUCCESS: Python version meets requirements{RESET}")
        return True

def check_virtual_env() -> bool:
    """Check if running in a virtual environment."""
    print_header("Virtual Environment Check")
    
    # Check if a virtual environment is active
    is_venv = sys.prefix != sys.base_prefix
    venv_path = os.environ.get('VIRTUAL_ENV')
    
    if is_venv:
        print(f"{GREEN}SUCCESS: Running in a virtual environment{RESET}")
        print(f"Virtual environment path: {venv_path}")
        
        # Check if the virtual environment follows the convention
        venv_name = os.path.basename(venv_path) if venv_path else None
        cwd = os.getcwd()
        standard_path = os.path.join(os.path.dirname(cwd), '.venv')
        
        if venv_name != '.venv':
            print(f"{YELLOW}WARNING: Virtual environment name is '{venv_name}' instead of '.venv'{RESET}")
            print(f"Tavren standard is to use '.venv' as the virtual environment name")
            print(f"See docs/DEVELOPMENT_SETUP.md for more details")
        
        return True
    else:
        print(f"{RED}ERROR: Not running in a virtual environment{RESET}")
        print("Please activate your virtual environment:")
        print("  Windows: .\.venv\\Scripts\\activate")
        print("  Unix/MacOS: source .venv/bin/activate")
        return False

def get_installed_packages() -> Dict[str, str]:
    """Get a dictionary of installed packages and their versions."""
    try:
        output = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], 
                                          universal_newlines=True)
        packages = {}
        for line in output.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==', 1)
                packages[name.lower()] = version
        return packages
    except subprocess.SubprocessError:
        print(f"{RED}ERROR: Failed to get installed packages{RESET}")
        return {}

def check_required_packages(verbose: bool = False) -> bool:
    """Check if all required packages are installed."""
    print_header("Required Packages Check")
    
    if not REQUIREMENTS_FILE.exists():
        print(f"{RED}ERROR: Requirements file not found at {REQUIREMENTS_FILE}{RESET}")
        return False
    
    try:
        # Read requirements file
        with open(REQUIREMENTS_FILE, 'r') as f:
            required_packages = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name and version
                    if '==' in line:
                        name, version = line.split('==', 1)
                        required_packages.append((name.lower(), version))
                    elif '>=' in line:
                        name, version = line.split('>=', 1)
                        required_packages.append((name.lower(), version))
                    else:
                        required_packages.append((line.lower(), None))
        
        # Get installed packages
        installed_packages = get_installed_packages()
        
        # Check if all required packages are installed
        missing_packages = []
        version_mismatch = []
        
        for name, required_version in required_packages:
            if name not in installed_packages:
                missing_packages.append(name)
            elif required_version and installed_packages[name] != required_version:
                version_mismatch.append((name, required_version, installed_packages[name]))
        
        # Print results
        if not missing_packages and not version_mismatch:
            print(f"{GREEN}SUCCESS: All required packages are installed with correct versions{RESET}")
            
            if verbose:
                print("\nInstalled packages:")
                for name, version in required_packages:
                    print(f"  {name}=={installed_packages.get(name, 'MISSING')}")
            
            return True
        else:
            if missing_packages:
                print(f"{RED}ERROR: Missing required packages:{RESET}")
                for name in missing_packages:
                    print(f"  - {name}")
            
            if version_mismatch:
                print(f"{YELLOW}WARNING: Package version mismatches:{RESET}")
                for name, required_version, installed_version in version_mismatch:
                    print(f"  - {name}: required {required_version}, installed {installed_version}")
            
            print("\nTo install missing packages:")
            print(f"  pip install -r {REQUIREMENTS_FILE}")
            
            return False
    
    except Exception as e:
        print(f"{RED}ERROR: Failed to check required packages: {e}{RESET}")
        return False

def check_disk_space() -> bool:
    """Check available disk space."""
    print_header("Disk Space Check")
    
    try:
        if platform.system() == 'Windows':
            # Windows-specific disk space check
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(os.getcwd()), None, None, ctypes.pointer(free_bytes))
            free_gb = free_bytes.value / (1024**3)
        else:
            # Unix-based disk space check
            import shutil
            free_gb = shutil.disk_usage(os.getcwd()).free / (1024**3)
        
        print(f"Available disk space: {free_gb:.2f} GB")
        
        if free_gb < 1:
            print(f"{RED}ERROR: Less than 1GB of free disk space available{RESET}")
            print("The Tavren backend requires at least 1GB of free space.")
            return False
        elif free_gb < 5:
            print(f"{YELLOW}WARNING: Less than 5GB of free disk space available{RESET}")
            print("For optimal development experience, at least 5GB is recommended.")
            return True
        else:
            print(f"{GREEN}SUCCESS: Sufficient disk space available{RESET}")
            return True
            
    except Exception as e:
        print(f"{YELLOW}WARNING: Could not check disk space: {e}{RESET}")
        return True

def main():
    """Main function to check the development environment."""
    parser = argparse.ArgumentParser(description="Check Tavren development environment")
    parser.add_argument("--skip-packages", action="store_true", 
                        help="Skip package validation (faster)")
    parser.add_argument("--verbose", action="store_true", 
                        help="Show more detailed output")
    args = parser.parse_args()
    
    print(f"{MAGENTA}Tavren Development Environment Checker{RESET}")
    print(f"Checking your environment configuration...\n")
    
    # Run checks
    python_check = check_python_version()
    venv_check = check_virtual_env()
    package_check = True if args.skip_packages else check_required_packages(args.verbose)
    space_check = check_disk_space()
    
    # Print summary
    print_header("Summary")
    
    checks = [
        ("Python Version", python_check),
        ("Virtual Environment", venv_check),
        ("Required Packages", package_check if not args.skip_packages else "SKIPPED"),
        ("Disk Space", space_check)
    ]
    
    for name, result in checks:
        if result is True:
            print(f"{name}: {GREEN}PASS{RESET}")
        elif result is False:
            print(f"{name}: {RED}FAIL{RESET}")
        else:
            print(f"{name}: {YELLOW}{result}{RESET}")
    
    # Final result
    if all(result is True for _, result in checks if result is not "SKIPPED"):
        print(f"\n{GREEN}Environment check passed successfully!{RESET}")
        return 0
    else:
        print(f"\n{YELLOW}Environment check completed with warnings or errors.{RESET}")
        print("Please address the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 