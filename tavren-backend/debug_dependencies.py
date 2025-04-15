#!/usr/bin/env python
"""
Debug script to identify problematic dependencies in FastAPI routers.
"""

import importlib
import sys
import traceback
from pathlib import Path

def test_import(module_path):
    """Try to import a module and print status."""
    print(f"Testing import: {module_path}")
    try:
        module = importlib.import_module(module_path)
        print(f"✓ Successfully imported {module_path}")
        return module
    except Exception as e:
        print(f"✗ Failed to import {module_path}")
        print(f"  Error: {e}")
        traceback.print_exc(file=sys.stdout)
        return None

def test_all_routers():
    """Test importing all routers individually."""
    router_modules = [
        'app.routers.static',
        'app.routers.consent',
        'app.routers.buyers',
        'app.routers.wallet',
        'app.routers.agent',
        'app.routers.data_packaging', 
        'app.routers.insight',
        'app.routers.dsr',
        'app.routers.user_router',
        'app.routers.buyer_data',
        'app.routers.llm_router',
        'app.routers.embedding_router',
        'app.routers.consent_ledger',
        'app.routers.consent_export',
        'app.routers.evaluation'
    ]
    
    for module_path in router_modules:
        test_import(module_path)
        print("-" * 80)

def test_service_dependencies():
    """Test importing all service dependencies."""
    service_modules = [
        'app.services.consent_ledger',
        'app.services.data_packaging',
        'app.services.data_service',
        'app.services.dsr_service',
        'app.services.embedding_service',
        'app.services.evaluation_service',
        'app.services.llm_service'
    ]
    
    for module_path in service_modules:
        test_import(module_path)
        print("-" * 80)

def test_schemas():
    """Test importing all schema modules."""
    schema_modules = [
        'app.schemas'
    ]
    
    for module_path in schema_modules:
        test_import(module_path)
        print("-" * 80)

def main():
    """Main function."""
    print("Starting dependency debugging process...")
    print("=" * 80)
    
    print("\nTesting individual routers:")
    test_all_routers()
    
    print("\nTesting service dependencies:")
    test_service_dependencies()
    
    print("\nTesting schemas:")
    test_schemas()
    
    print("\nAttempting to import FastAPI app:")
    test_import('app.main')
    
    print("\nDebug process complete.")

if __name__ == "__main__":
    main() 