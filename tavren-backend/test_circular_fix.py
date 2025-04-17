"""
Test script to verify that circular import issues have been fixed.
"""
import sys
import os
import logging

# Set up logging to see any import errors
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Try importing modules in order to test for circular dependencies."""
    try:
        logger.info("Testing import of app.dependencies...")
        from app import dependencies
        logger.info("✅ Successfully imported app.dependencies")
        
        logger.info("Testing import of app.auth...")
        from app import auth
        logger.info("✅ Successfully imported app.auth")
        
        logger.info("Testing import of app.utils.rate_limit...")
        from app.utils import rate_limit
        logger.info("✅ Successfully imported app.utils.rate_limit")
        
        logger.info("Testing import of app.routers.consent_export...")
        from app.routers import consent_export
        logger.info("✅ Successfully imported app.routers.consent_export")
        
        logger.info("Testing import of app.routers.consent_ledger...")
        from app.routers import consent_ledger
        logger.info("✅ Successfully imported app.routers.consent_ledger")
        
        logger.info("Testing joint import of auth and dependencies...")
        from app import auth, dependencies
        logger.info("✅ Successfully imported both auth and dependencies together")
        
        logger.info("All import tests passed! Circular dependencies have been resolved.")
        return True
    except Exception as e:
        logger.error(f"❌ Import test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 