#!/usr/bin/env python3
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the parent directory to sys.path to allow imports from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.export_verifier import ExportVerifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
log = logging.getLogger("export_verifier_cli")

def main():
    parser = argparse.ArgumentParser(description="Verify Tavren consent export files")
    parser.add_argument("export_file", help="Path to the export JSON file to verify")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        log.setLevel(logging.DEBUG)
    
    log.info(f"Verifying export file: {args.export_file}")
    
    verifier = ExportVerifier()
    verified, message = verifier.verify_export_file(args.export_file)
    
    if verified:
        log.info(f"✓ Verification successful: {message}")
        
        # Print additional export details if verbose
        if args.verbose:
            try:
                with open(args.export_file, 'r') as f:
                    export_data = json.load(f)
                    
                user_id = export_data.get("user_id", "Unknown")
                timestamp = export_data.get("export_timestamp", "Unknown")
                event_count = len(export_data.get("consent_events", []))
                dsr_count = len(export_data.get("dsr_actions", []))
                pet_count = len(export_data.get("pet_queries", []))
                
                log.info(f"Export details:")
                log.info(f"  User ID: {user_id}")
                log.info(f"  Export timestamp: {timestamp}")
                log.info(f"  Consent events: {event_count}")
                log.info(f"  DSR actions: {dsr_count}")
                log.info(f"  PET queries: {pet_count}")
            except Exception as e:
                log.error(f"Error reading export details: {e}")
        
        return 0
    else:
        log.error(f"✗ Verification failed: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 