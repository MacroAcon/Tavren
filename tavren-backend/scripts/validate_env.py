#!/usr/bin/env python3
"""
Environment Variable Validator for Tavren

This script validates that all required environment variables are set
and properly formatted before deployment or running the application.

Usage:
    python validate_env.py [--env-file .env] [--mode production|staging|development]
"""

import os
import sys
import re
import argparse
from collections import namedtuple
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Define colors for terminal output
RESET = "\033[0m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"

# Define a variable requirement structure
EnvVar = namedtuple("EnvVar", ["name", "required", "regex", "description", "example"])

# Define required environment variables by category
DATABASE_VARS = [
    EnvVar(
        "DATABASE_URL", 
        True, 
        r"^(postgresql|sqlite)(\+[a-z]+)?://.*$",
        "Database connection string",
        "postgresql+asyncpg://user:password@host:5432/dbname"
    ),
    EnvVar(
        "POSTGRES_USER_SECRET", 
        False, 
        r"^[a-zA-Z0-9_]+$",
        "PostgreSQL username for Docker deployment",
        "tavren_user"
    ),
    EnvVar(
        "POSTGRES_PASSWORD_SECRET", 
        False, 
        r".{8,}",
        "PostgreSQL password for Docker deployment (min 8 chars)",
        "strong-random-password"
    ),
]

SECURITY_VARS = [
    EnvVar(
        "JWT_SECRET_KEY", 
        True, 
        r"^[0-9a-f]{32,}$",
        "32+ character hex string for JWT token signing",
        "d8b3a538f5c1489d8c2581a0db963327"
    ),
    EnvVar(
        "DATA_ENCRYPTION_KEY", 
        True, 
        r"^[0-9a-f]{32,}$",
        "32+ character hex string for data encryption",
        "62c9b2e9a9f64cfd81bf0d0a9e5aeb96"
    ),
    EnvVar(
        "ADMIN_API_KEY", 
        True, 
        r"^[0-9a-f]{24,}$",
        "24+ character hex string for admin API authentication",
        "d8b3a538f5c1489d8c2581a0"
    ),
]

APPLICATION_VARS = [
    EnvVar(
        "ACCESS_TOKEN_EXPIRE_MINUTES", 
        False, 
        r"^\d+$",
        "JWT token expiration time in minutes",
        "30"
    ),
    EnvVar(
        "MINIMUM_PAYOUT_THRESHOLD", 
        False, 
        r"^\d+(\.\d+)?$",
        "Minimum amount for payouts",
        "5.00"
    ),
    EnvVar(
        "LOG_LEVEL", 
        False, 
        r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        "Application logging level",
        "INFO"
    ),
    EnvVar(
        "ENVIRONMENT", 
        True, 
        r"^(development|staging|production)$",
        "Deployment environment",
        "production"
    ),
]

EXTERNAL_SERVICES = [
    EnvVar(
        "NVIDIA_API_KEY", 
        False, 
        r"^[A-Za-z0-9_\-]{16,}$",
        "API key for NVIDIA services (if used)",
        "nvapi-abc123xyz789"
    ),
    EnvVar(
        "REDIS_PASSWORD", 
        False, 
        r".{8,}",
        "Redis password for caching (if used)",
        "strong-redis-password"
    ),
]

# Group all variable categories
ALL_VARS = DATABASE_VARS + SECURITY_VARS + APPLICATION_VARS + EXTERNAL_SERVICES

def load_env_file(env_file: str) -> Dict[str, str]:
    """Load variables from a .env file."""
    env_vars = {}
    
    if not os.path.exists(env_file):
        print(f"{RED}Error: Environment file {env_file} not found{RESET}")
        return env_vars
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, *value_parts = line.split('=', 1)
            if value_parts:
                value = value_parts[0].strip()
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                env_vars[key.strip()] = value
    
    return env_vars

def validate_variables(env_vars: Dict[str, str], mode: str, all_vars: List[EnvVar]) -> Tuple[int, int, int]:
    """Validate that all required variables are set and properly formatted."""
    passed = 0
    warnings = 0
    errors = 0
    
    # Filter variables based on mode
    check_vars = all_vars
    if mode == "development":
        # In development, make fewer variables required
        check_vars = [
            EnvVar(var.name, False if var.name in [
                "NVIDIA_API_KEY", 
                "REDIS_PASSWORD",
                "POSTGRES_PASSWORD_SECRET"
            ] else var.required, 
            var.regex, var.description, var.example) 
            for var in all_vars
        ]
    
    print(f"\n{BLUE}Environment Validation for {mode.upper()} mode{RESET}")
    print("-" * 60)
    
    # Group by category for nicer output
    categories = [
        ("Database Configuration", DATABASE_VARS),
        ("Security Settings", SECURITY_VARS),
        ("Application Settings", APPLICATION_VARS),
        ("External Services", EXTERNAL_SERVICES),
    ]
    
    for category_name, category_vars in categories:
        print(f"\n{BLUE}{category_name}:{RESET}")
        for var in category_vars:
            # Check if variable exists
            if var.name not in env_vars or not env_vars[var.name]:
                if var.required and (mode != "development" or var.name in ["JWT_SECRET_KEY", "ENVIRONMENT"]):
                    print(f"  {RED}ERROR: {var.name} is required but not set{RESET}")
                    print(f"    Description: {var.description}")
                    print(f"    Example: {var.example}")
                    errors += 1
                else:
                    print(f"  {YELLOW}WARNING: {var.name} is not set{RESET}")
                    print(f"    Description: {var.description}")
                    warnings += 1
                continue
                
            # Check format if regex is provided
            value = env_vars[var.name]
            if var.regex and not re.match(var.regex, value):
                print(f"  {RED}ERROR: {var.name} has invalid format{RESET}")
                print(f"    Current: {value}")
                print(f"    Expected format: {var.description}")
                print(f"    Example: {var.example}")
                errors += 1
            else:
                # Warn about default/weak values in production
                if mode == "production" and var.name in ["JWT_SECRET_KEY", "DATA_ENCRYPTION_KEY", "ADMIN_API_KEY"]:
                    if value.lower() in ["your_secret_key", "your_key", "your_api_key", "changeme", "secret", "key"]:
                        print(f"  {RED}ERROR: {var.name} appears to be a default value{RESET}")
                        print(f"    Please generate a proper secret for production use")
                        errors += 1
                    elif len(value) < 16:
                        print(f"  {YELLOW}WARNING: {var.name} appears to be weak (too short){RESET}")
                        warnings += 1
                else:
                    print(f"  {GREEN}OK: {var.name}{RESET}")
                    passed += 1
    
    return passed, warnings, errors

def suggest_missing_vars(env_vars: Dict[str, str], all_vars: List[EnvVar], mode: str) -> None:
    """Suggest commands to generate missing but required variables."""
    missing_vars = []
    
    for var in all_vars:
        if var.required and (var.name not in env_vars or not env_vars[var.name]):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n{YELLOW}Suggested commands to generate missing variables:{RESET}")
        
        for var in missing_vars:
            if var.name == "JWT_SECRET_KEY":
                print(f"  JWT_SECRET_KEY=$(openssl rand -hex 32)")
            elif var.name == "DATA_ENCRYPTION_KEY":
                print(f"  DATA_ENCRYPTION_KEY=$(openssl rand -hex 16)")
            elif var.name == "ADMIN_API_KEY":
                print(f"  ADMIN_API_KEY=$(openssl rand -hex 24)")
            elif var.name == "POSTGRES_PASSWORD_SECRET":
                print(f"  POSTGRES_PASSWORD_SECRET=$(openssl rand -base64 18 | tr -d '+/=' | cut -c1-16)")
            elif var.name == "REDIS_PASSWORD":
                print(f"  REDIS_PASSWORD=$(openssl rand -base64 18 | tr -d '+/=' | cut -c1-16)")
            elif var.name == "DATABASE_URL":
                if mode == "production":
                    print(f"  # Set DATABASE_URL to your PostgreSQL connection string")
                    print(f"  DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname")
                else:
                    print(f"  DATABASE_URL=sqlite+aiosqlite:///./tavren_dev.db")
            elif var.name == "ENVIRONMENT":
                print(f"  ENVIRONMENT={mode}")
        
        print("\nAdd these to your .env file or export them in your shell before running the application.")

def main():
    parser = argparse.ArgumentParser(description="Validate Tavren environment variables")
    parser.add_argument("--env-file", "-e", default=".env", help="Path to .env file (default: .env)")
    parser.add_argument("--mode", "-m", choices=["development", "staging", "production"], default="production",
                        help="Deployment mode (default: production)")
    args = parser.parse_args()

    # Load variables from .env file
    env_file = args.env_file
    mode = args.mode
    
    # First check if we can find the env file
    if not os.path.exists(env_file):
        print(f"{YELLOW}Warning: {env_file} not found, checking common locations...{RESET}")
        
        # Try to locate .env file in parent directories
        current_dir = Path.cwd()
        found = False
        
        # Try the tavren-backend directory if we're in a subdirectory
        if "tavren-backend" in str(current_dir):
            root_dir = current_dir
            while "tavren-backend" in str(root_dir):
                if (root_dir / ".env").exists():
                    env_file = str(root_dir / ".env")
                    found = True
                    break
                if root_dir.parent == root_dir:
                    break
                root_dir = root_dir.parent
        
        if not found:
            print(f"{YELLOW}No .env file found, using current environment variables...{RESET}")

    # Load from env file if it exists, otherwise use os.environ
    if os.path.exists(env_file):
        print(f"Loading variables from {env_file}")
        env_vars = load_env_file(env_file)
    else:
        env_vars = {}
    
    # Merge with environment variables (environment takes precedence)
    for var in ALL_VARS:
        if var.name in os.environ:
            env_vars[var.name] = os.environ[var.name]
    
    # Validate the variables
    passed, warnings, errors = validate_variables(env_vars, mode, ALL_VARS)
    
    # Provide a summary
    print("\n" + "-" * 60)
    print(f"{BLUE}Validation Summary:{RESET}")
    print(f"  {GREEN}Passed: {passed}{RESET}")
    print(f"  {YELLOW}Warnings: {warnings}{RESET}")
    print(f"  {RED}Errors: {errors}{RESET}")
    
    # Suggest missing variables
    if errors > 0:
        suggest_missing_vars(env_vars, ALL_VARS, mode)
    
    # Exit with appropriate code
    if errors > 0:
        print(f"\n{RED}Validation failed with {errors} errors. Please fix before deployment.{RESET}")
        sys.exit(1)
    elif warnings > 0:
        print(f"\n{YELLOW}Validation passed with {warnings} warnings. Review before deployment.{RESET}")
        sys.exit(0)
    else:
        print(f"\n{GREEN}All environment variables validated successfully!{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main() 