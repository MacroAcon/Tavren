#!/usr/bin/env python
"""
Script to fix service dependency functions to use Depends(get_db) instead
of explicit AsyncSession type annotations.

This script finds all Python files in the app directory and replaces 
any service dependency functions that use AsyncSession type annotations
with versions that use Depends(get_db) instead.

Usage:
    python fix_service_dependencies.py
"""

import os
import re
from pathlib import Path

def fix_service_dependency(content):
    """
    Find and fix service dependency function patterns in file content.
    
    Looks for functions like:
    async def get_X_service(db: AsyncSession) -> XService:
        return XService(db)
    
    And updates them to:
    async def get_X_service(db = Depends(get_db)) -> XService:
        return XService(db)
    
    Also adds necessary imports if they're missing.
    """
    # First check if we need to add imports
    imports_to_add = []
    
    if "from fastapi import Depends" not in content and "from fastapi import " in content:
        # Add Depends to existing fastapi import
        content = re.sub(
            r"from fastapi import (.+)",
            r"from fastapi import \1, Depends",
            content
        )
    elif "from fastapi import" not in content and "import fastapi" not in content:
        imports_to_add.append("from fastapi import Depends")
        
    if "from app.database import get_db" not in content and "import app.database" not in content:
        imports_to_add.append("from app.database import get_db")
    
    # Find patterns like: async def get_X_service(db: AsyncSession) -> XService:
    pattern = re.compile(
        r"(async\s+def\s+get_\w+(?:_service|_validator|_limiter)\s*\(\s*)db\s*:\s*(?:\")?AsyncSession(?:\")?\s*(?:=\s*[^)]+)?\)(\s*->)",
        re.MULTILINE
    )
    replacement = r"\1db = Depends(get_db))\2"
    fixed_content = pattern.sub(replacement, content)
    
    # Add imports if needed
    if imports_to_add and fixed_content != content:
        # Find the last import statement
        import_section_end = 0
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_section_end = i

        # Insert new imports after the last import
        for imp in imports_to_add:
            if import_section_end > 0:
                lines.insert(import_section_end + 1, imp)
                import_section_end += 1
            else:
                # If no imports found, add at the beginning of the file
                lines.insert(0, imp)
                import_section_end = 0
        
        fixed_content = "\n".join(lines)
    
    return fixed_content

def process_file(file_path):
    """Process a single file, fixing service dependency functions."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "async def get_" in content and "AsyncSession" in content:
            fixed_content = fix_service_dependency(content)
            
            # Only write back if changes were made
            if fixed_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"Fixed: {file_path}")
                return True
                
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to find and process all Python files."""
    base_dir = Path.cwd() / 'app'
    if not base_dir.exists():
        print(f"Directory {base_dir} not found")
        return
    
    changed_files = 0
    
    for file_path in base_dir.glob('**/*.py'):
        if process_file(file_path):
            changed_files += 1
    
    print(f"Fixed service dependency functions in {changed_files} files")

if __name__ == "__main__":
    main() 