#!/usr/bin/env python3
"""
Secrets Synchronization Tool for Tavren

This script syncs environment variables from local .env files to cloud platforms.
Currently supports Render and Vercel through their APIs.

Prerequisites:
- Render API token in RENDER_API_TOKEN environment variable
- Vercel API token in VERCEL_API_TOKEN environment variable

Usage:
    python sync_secrets.py [--env-file .env.production] [--platform render,vercel]
"""

import os
import sys
import argparse
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

# ANSI color codes for output
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"

# Default cloud service IDs - replace with your actual IDs
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID", "srv-xyz123")
VERCEL_PROJECT_ID = os.environ.get("VERCEL_PROJECT_ID", "prj-xyz123")

# API configuration
RENDER_API_BASE = "https://api.render.com/v1"
VERCEL_API_BASE = "https://api.vercel.com/v9"

def load_env_file(env_file: str) -> Dict[str, str]:
    """Load variables from a .env file."""
    if not os.path.exists(env_file):
        print(f"{RED}Error: Environment file {env_file} not found{RESET}")
        sys.exit(1)
    
    env_vars = {}
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

def filter_vars_for_platform(env_vars: Dict[str, str], platform: str) -> Dict[str, str]:
    """Filter environment variables based on platform-specific requirements."""
    # Variables to exclude from certain platforms
    render_exclude = {'NODE_ENV', 'VERCEL', 'VERCEL_ENV'}
    vercel_exclude = {'RENDER', 'DATABASE_URL'}
    
    filtered_vars = env_vars.copy()
    
    if platform == "render":
        for key in render_exclude:
            if key in filtered_vars:
                del filtered_vars[key]
    
    elif platform == "vercel":
        for key in vercel_exclude:
            if key in filtered_vars:
                del filtered_vars[key]
                
        # For Vercel, add NEXT_ prefix to certain variables if needed
        # (Adjust as needed for your specific project)
        next_prefixed = {}
        for key, value in filtered_vars.items():
            if key.startswith('VITE_'):
                # Convert VITE_ prefixes to NEXT_PUBLIC_ for Next.js
                next_key = f"NEXT_PUBLIC_{key[5:]}"
                next_prefixed[next_key] = value
                
        filtered_vars.update(next_prefixed)
    
    return filtered_vars

def sync_to_render(env_vars: Dict[str, str], dry_run: bool = False) -> bool:
    """Sync environment variables to Render."""
    api_token = os.environ.get("RENDER_API_TOKEN")
    if not api_token:
        print(f"{RED}Error: RENDER_API_TOKEN environment variable not set{RESET}")
        print("Please set it with: export RENDER_API_TOKEN=your_token")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    service_id = RENDER_SERVICE_ID
    url = f"{RENDER_API_BASE}/services/{service_id}/env-vars"
    
    # First get existing env vars
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        existing_env = {item['key']: item['id'] for item in response.json()}
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error fetching existing Render environment variables: {e}{RESET}")
        return False
    
    if dry_run:
        print(f"\n{YELLOW}DRY RUN: Would update these variables on Render:{RESET}")
        for key, value in env_vars.items():
            masked_value = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else "***"
            print(f"  {key}={masked_value}")
        return True
    
    # Update or create env vars
    env_var_updates = []
    for key, value in env_vars.items():
        if key in existing_env:
            # Update existing variable
            env_var_updates.append({
                "id": existing_env[key],
                "key": key, 
                "value": value
            })
        else:
            # Create new variable
            env_var_updates.append({
                "key": key,
                "value": value
            })
    
    try:
        response = requests.put(
            url, 
            headers=headers,
            json=env_var_updates
        )
        response.raise_for_status()
        print(f"{GREEN}Successfully updated {len(env_var_updates)} environment variables on Render{RESET}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error updating Render environment variables: {e}{RESET}")
        return False

def sync_to_vercel(env_vars: Dict[str, str], dry_run: bool = False) -> bool:
    """Sync environment variables to Vercel."""
    api_token = os.environ.get("VERCEL_API_TOKEN")
    if not api_token:
        print(f"{RED}Error: VERCEL_API_TOKEN environment variable not set{RESET}")
        print("Please set it with: export VERCEL_API_TOKEN=your_token")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    project_id = VERCEL_PROJECT_ID
    url = f"{VERCEL_API_BASE}/projects/{project_id}/env"
    
    # First get existing env vars
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        existing_env = {item['key']: item['id'] for item in response.json().get('envs', [])}
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error fetching existing Vercel environment variables: {e}{RESET}")
        return False
    
    if dry_run:
        print(f"\n{YELLOW}DRY RUN: Would update these variables on Vercel:{RESET}")
        for key, value in env_vars.items():
            masked_value = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else "***"
            print(f"  {key}={masked_value}")
        return True
    
    # Update each variable individually (Vercel API requirement)
    success_count = 0
    for key, value in env_vars.items():
        try:
            if key in existing_env:
                # Update existing variable
                update_url = f"{url}/{existing_env[key]}"
                payload = {
                    "value": value,
                    "target": ["production", "preview", "development"]
                }
                response = requests.patch(update_url, headers=headers, json=payload)
            else:
                # Create new variable
                payload = {
                    "key": key,
                    "value": value,
                    "target": ["production", "preview", "development"],
                    "type": "plain" # Use encrypted for sensitive data
                }
                response = requests.post(url, headers=headers, json=payload)
            
            response.raise_for_status()
            success_count += 1
        except requests.exceptions.RequestException as e:
            print(f"{RED}Error updating Vercel environment variable {key}: {e}{RESET}")
    
    if success_count > 0:
        print(f"{GREEN}Successfully updated {success_count} environment variables on Vercel{RESET}")
        return True
    else:
        print(f"{RED}Failed to update any environment variables on Vercel{RESET}")
        return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Sync environment variables to cloud platforms")
    parser.add_argument("--env-file", default=".env.production", 
                        help="Path to the environment file (default: .env.production)")
    parser.add_argument("--platform", default="render,vercel",
                        help="Comma-separated list of platforms to sync to (default: render,vercel)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be synced without making any changes")
    parser.add_argument("--render-service-id", 
                        help="Render service ID (overrides RENDER_SERVICE_ID env var)")
    parser.add_argument("--vercel-project-id",
                        help="Vercel project ID (overrides VERCEL_PROJECT_ID env var)")
    args = parser.parse_args()
    
    # Update service IDs if provided
    global RENDER_SERVICE_ID, VERCEL_PROJECT_ID
    if args.render_service_id:
        RENDER_SERVICE_ID = args.render_service_id
    if args.vercel_project_id:
        VERCEL_PROJECT_ID = args.vercel_project_id
    
    # Load environment variables
    env_vars = load_env_file(args.env_file)
    print(f"{BLUE}Loaded {len(env_vars)} variables from {args.env_file}{RESET}")
    
    platforms = [p.strip() for p in args.platform.split(",")]
    results = {}
    
    for platform in platforms:
        if platform not in ["render", "vercel"]:
            print(f"{YELLOW}Warning: Unknown platform '{platform}'. Skipping...{RESET}")
            continue
        
        print(f"\n{BLUE}Syncing environment variables to {platform.upper()}...{RESET}")
        platform_vars = filter_vars_for_platform(env_vars, platform)
        
        if platform == "render":
            results[platform] = sync_to_render(platform_vars, args.dry_run)
        elif platform == "vercel":
            results[platform] = sync_to_vercel(platform_vars, args.dry_run)
    
    # Print summary
    print(f"\n{BLUE}Synchronization Summary:{RESET}")
    for platform, success in results.items():
        status = f"{GREEN}SUCCESS{RESET}" if success else f"{RED}FAILED{RESET}"
        print(f"  {platform.upper()}: {status}")
    
    if args.dry_run:
        print(f"\n{YELLOW}This was a dry run. No changes were made.{RESET}")
    
    # Exit with an error code if any sync failed
    if not all(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    main() 