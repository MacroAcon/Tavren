import json
import logging
import hashlib
import hmac
from typing import Dict, Any, Tuple, Optional

# Set up logging
log = logging.getLogger("app")

class ExportVerifier:
    """
    Utility class for verifying the integrity and authenticity of consent exports.
    """
    
    def __init__(self):
        self._signing_key = self._load_signing_key()
    
    def _load_signing_key(self) -> Optional[bytes]:
        """Load the signing key from environment or secure storage."""
        # In production, this would load from a secure location
        # For now, use a hardcoded key (REPLACE IN PRODUCTION)
        try:
            # This is just a placeholder - in production, use env vars or secure storage
            return b"tavren-consent-export-signing-key-2023"
        except Exception as e:
            log.warning(f"Failed to load signing key: {str(e)}")
            return None
    
    def verify_export(self, export_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify the integrity and authenticity of an export package.
        
        Args:
            export_data: The export package to verify
            
        Returns:
            A tuple of (is_verified, message)
        """
        if not isinstance(export_data, dict):
            return False, "Invalid export format: must be a JSON object"
        
        # Check if export contains verification section
        if "verification" not in export_data:
            return False, "Export missing verification section"
        
        verification = export_data["verification"]
        
        # Check for required verification fields
        if "ledger_hash" not in verification:
            return False, "Export missing hash"
        
        # Extract the hash from verification
        claimed_hash = verification["ledger_hash"]
        
        # Create a copy without the verification section for hash calculation
        export_copy = export_data.copy()
        if "verification" in export_copy:
            del export_copy["verification"]
        
        # Calculate the actual hash
        json_str = json.dumps(export_copy, sort_keys=True)
        hash_obj = hashlib.sha256(json_str.encode())
        calculated_hash = hash_obj.hexdigest()
        
        # Compare the hashes
        if calculated_hash != claimed_hash:
            return False, "Hash verification failed: export may have been tampered with"
        
        # Check signature if present
        if "digital_signature" in verification and self._signing_key:
            if "signature_method" not in verification:
                return False, "Export has signature but no signature method specified"
            
            signature_method = verification["signature_method"]
            claimed_signature = verification["digital_signature"]
            
            if signature_method == "HMAC-SHA256":
                expected_signature = hmac.new(
                    key=self._signing_key,
                    msg=claimed_hash.encode(),
                    digestmod=hashlib.sha256
                ).hexdigest()
                
                if expected_signature != claimed_signature:
                    return False, "Signature verification failed: export may not be authentic"
            else:
                return False, f"Unsupported signature method: {signature_method}"
        
        return True, "Export verified successfully"
    
    def verify_export_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Verify an export from a file.
        
        Args:
            file_path: Path to the export file
            
        Returns:
            A tuple of (is_verified, message)
        """
        try:
            with open(file_path, 'r') as f:
                export_data = json.load(f)
                return self.verify_export(export_data)
        except Exception as e:
            return False, f"Error verifying export file: {str(e)}" 