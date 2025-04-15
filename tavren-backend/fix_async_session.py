#!/usr/bin/env python
"""
Script to fix AsyncSession type annotations in FastAPI route handlers.

This script finds all route files in the project and removes the explicit
AsyncSession type annotation from database dependency injections, replacing them
with just the Depends(get_db) call without type annotation.

Usage:
    python fix_async_session.py
"""

import os
import re
from pathlib import Path

def process_file(file_path):
    """Process a single file, fixing AsyncSession type annotations."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match AsyncSession type annotations
        pattern = re.compile(r'db\s*:\s*AsyncSession\s*=\s*Depends\(\s*get_db\s*\)')
        modified_content = pattern.sub('db = Depends(get_db)', content)
        
        # Other patterns to check
        other_patterns = [
            (re.compile(r'db\s*:\s*"AsyncSession"\s*=\s*Depends\(\s*get_db\s*\)'), 'db = Depends(get_db)'),
            (re.compile(r'db\s*:\s*Optional\[\s*AsyncSession\s*\]\s*=\s*Depends\(\s*get_db\s*\)'), 'db = Depends(get_db)'),
            (re.compile(r'db\s*:\s*Optional\[\s*"AsyncSession"\s*\]\s*=\s*Depends\(\s*get_db\s*\)'), 'db = Depends(get_db)')
        ]
        
        for pattern, replacement in other_patterns:
            modified_content = pattern.sub(replacement, modified_content)
        
        # Only write back if changes were made
        if modified_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"Fixed: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to find and process all router files."""
    # Directories to search for router files
    search_dirs = [
        'app/routers',
        'app/services',
        'app/utils',
        'app'
    ]
    
    base_dir = Path.cwd()
    changed_files = 0
    
    for search_dir in search_dirs:
        dir_path = base_dir / search_dir
        if not dir_path.exists():
            print(f"Directory {dir_path} not found")
            continue
        
        print(f"Processing files in {dir_path}")
        for file_path in dir_path.glob('**/*.py'):
            if process_file(file_path):
                changed_files += 1
    
    print(f"Fixed AsyncSession type annotations in {changed_files} files")

if __name__ == "__main__":
    main() 