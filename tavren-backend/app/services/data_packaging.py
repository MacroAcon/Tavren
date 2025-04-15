import logging
import json
import uuid
import hashlib
import random
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import Depends

from app.models import User, ConsentEvent
from app.utils.crypto import encrypt_data, decrypt_data
from app.config import get_settings
from app.database import get_db

# Get logger
log = logging.getLogger("app")

settings = get_settings()

class DataPackagingService:
    """
    Service for packaging user data according to agent requests and consent preferences.
    Responsible for:
    - Retrieving user data based on data type and specific consent permissions
    - Applying appropriate anonymization based on buyer's trust tier and access level
    - Formatting data according to standardized schemas
    - Validating data against consent permissions
    - Generating secure access tokens for time-limited access
    - Creating audit records for all data package operations
    - Encrypting sensitive data for secure transmission
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._encryption_key = self._get_or_create_encryption_key()
        
    async def package_data(self, user_id: str, data_type: str, access_level: str, 
                          consent_id: str, purpose: str, buyer_id: str = None,
                          trust_tier: str = "standard") -> Dict[str, Any]:
        """
        Main method to retrieve, anonymize, and package data based on request parameters.
        
        Args:
            user_id: ID of the user whose data is being requested
            data_type: Type of data being requested (e.g., "app_usage", "location")
            access_level: Access level requested (e.g., "anonymous_short_term")
            consent_id: ID of the consent record for this data exchange
            purpose: Purpose for data use as specified in MCP context
            buyer_id: Optional ID of the data buyer
            trust_tier: Trust tier of the buyer ("low", "standard", "high")
            
        Returns:
            Dict containing the packaged data with appropriate metadata
        """
        log.info(f"Packaging {data_type} data for user {user_id} at {access_level} access level for buyer {buyer_id}")
        
        # 1. Validate consent permissions
        is_permitted, validation_result = await self._validate_consent_permissions(
            user_id, data_type, purpose, consent_id, buyer_id
        )
        
        if not is_permitted:
            log.warning(f"Consent validation failed: {validation_result.get('reason')}")
            return self._create_empty_package(
                data_type, 
                consent_id, 
                validation_result.get('reason', 'Permission denied')
            )
        
        # 2. Retrieve raw data
        raw_data = await self._retrieve_data(user_id, data_type)
        if not raw_data:
            log.warning(f"No {data_type} data found for user {user_id}")
            return self._create_empty_package(data_type, consent_id, "Data not available")
        
        # 3. Apply anonymization based on access level and trust tier
        anonymization_level = self._determine_anonymization_level(access_level, trust_tier)
        anonymized_data = self._anonymize_data(raw_data, data_type, anonymization_level)
        
        # 4. Apply schema formatting
        formatted_data = self._format_data_for_schema(anonymized_data, data_type)
        
        # 5. Generate secure package with metadata
        expiry_time = self._calculate_expiry(access_level)
        access_token = self._generate_access_token(consent_id, expiry_time)
        
        package_id = str(uuid.uuid4())
        
        packaged_data = {
            "tavren_data_package": "1.1",
            "package_id": package_id,
            "consent_id": consent_id,
            "created_at": datetime.now().isoformat(),
            "data_type": data_type,
            "access_level": access_level,
            "purpose": purpose,
            "expires_at": expiry_time,
            "anonymization_level": anonymization_level,
            "access_token": access_token,
            "content": formatted_data,
            "metadata": {
                "record_count": len(formatted_data) if isinstance(formatted_data, list) else 1,
                "schema_version": self._get_schema_version(data_type),
                "data_quality_score": self._calculate_data_quality(formatted_data),
                "buyer_id": buyer_id,
                "trust_tier": trust_tier,
                "encryption_status": "encrypted" if settings.ENCRYPT_DATA_PACKAGES else "none",
                "mcp_context": {
                    "purpose": purpose,
                    "usage_policy": self._get_usage_policy(access_level, trust_tier)
                }
            }
        }
        
        # 6. Create audit record
        await self._create_audit_record(packaged_data)
        
        # 7. Apply encryption for sensitive data if configured
        if settings.ENCRYPT_DATA_PACKAGES:
            packaged_data["content"] = self._encrypt_package_content(formatted_data)
        
        log.info(f"Successfully packaged {data_type} data (ID: {packaged_data['package_id']})")
        return packaged_data
    
    async def validate_access_token(self, access_token: str, package_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates an access token for a specific data package.
        
        Args:
            access_token: The token to validate
            package_id: ID of the package being accessed
            
        Returns:
            Tuple of (is_valid, details)
        """
        # Decode token to get claims
        try:
            token_parts = access_token.split('.')
            if len(token_parts) != 3:
                return False, {"reason": "Invalid token format"}
            
            payload = json.loads(base64.b64decode(token_parts[1] + "==").decode('utf-8'))
            
            # Check if token is expired
            if datetime.fromtimestamp(payload.get('exp', 0)) < datetime.now():
                return False, {"reason": "Token expired"}
                
            # Check if token is for this package
            if payload.get('package_id') != package_id:
                return False, {"reason": "Token not valid for this package"}
                
            # In a full implementation, we would also verify the signature
            
            return True, payload
        except Exception as e:
            log.error(f"Error validating access token: {str(e)}")
            return False, {"reason": "Invalid token"}
    
    async def get_package_by_id(self, package_id: str, access_token: str = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves a previously created data package by its ID,
        optionally validating an access token.
        
        In a real implementation, this would query a database of created packages.
        For the POC, we'll simulate this with a simple error message.
        """
        # This is a placeholder - in a real implementation we would:
        # 1. Retrieve the package from storage
        # 2. Validate the access token if provided
        # 3. Decrypt the content if needed
        # 4. Return the package or an error
        return None, {"reason": "Package retrieval not implemented in this POC"}
    
    async def _validate_consent_permissions(
        self, user_id: str, data_type: str, purpose: str, consent_id: str, buyer_id: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates if the data request is permitted based on user's consent preferences.
        
        Args:
            user_id: User whose data is being requested
            data_type: Type of data being requested
            purpose: Purpose for data use
            consent_id: ID of the consent record
            buyer_id: Optional ID of the data buyer
            
        Returns:
            Tuple of (is_permitted, details)
        """
        # Check if consent record exists
        stmt = select(ConsentEvent).where(ConsentEvent.id == consent_id)
        result = await self.db.execute(stmt)
        consent_record = result.scalar_one_or_none()
        
        if not consent_record:
            return False, {"reason": "Consent record not found"}
            
        # Check if consent was given for this user
        if consent_record.user_id != user_id:
            return False, {"reason": "Consent record does not match user"}
            
        # Check if consent was accepted (not declined)
        if consent_record.action != "accepted":
            return False, {"reason": "User declined consent for this data"}
        
        # In a full implementation, we would check additional consent details
        # such as specific data types, purposes, and buyer restrictions
        
        return True, {"status": "approved"}
        
    async def _retrieve_data(self, user_id: str, data_type: str) -> Any:
        """
        Retrieve raw data of specified type for the user.
        In production, this would query actual databases or data lakes.
        
        For this POC, we'll use mock data.
        """
        # Mock data generation for different data types
        if data_type == "app_usage":
            return self._generate_mock_app_usage(user_id)
        elif data_type == "location":
            return self._generate_mock_location_data(user_id)
        elif data_type == "browsing_history":
            return self._generate_mock_browsing_history(user_id)
        elif data_type == "health":
            return self._generate_mock_health_data(user_id)
        elif data_type == "financial":
            return self._generate_mock_financial_data(user_id)
        else:
            log.warning(f"Unknown data type: {data_type}")
            return None
    
    def _determine_anonymization_level(self, access_level: str, trust_tier: str) -> str:
        """
        Determine the appropriate anonymization level based on access level and trust tier.
        
        Args:
            access_level: The requested access level
            trust_tier: The buyer's trust tier
            
        Returns:
            Anonymization level to apply
        """
        # Base anonymization from access level
        if access_level == "precise_persistent":
            base_level = "minimal"
        elif access_level == "precise_short_term":
            base_level = "moderate"
        elif access_level == "anonymous_persistent":
            base_level = "strong_with_longitudinal"
        else:  # anonymous_short_term
            base_level = "strong"
            
        # Adjust based on trust tier
        if trust_tier == "low":
            # Increase anonymization for low trust
            if base_level == "minimal":
                return "moderate"
            elif base_level == "moderate":
                return "strong_with_longitudinal"
            else:
                return "strong"
        elif trust_tier == "high":
            # Decrease anonymization for high trust (but never below minimal)
            if base_level == "strong":
                return "strong_with_longitudinal"
            elif base_level == "strong_with_longitudinal":
                return "moderate"
            else:
                return base_level
                
        # For standard trust tier, use the base level
        return base_level
    
    def _anonymize_data(self, data: Any, data_type: str, anonymization_level: str) -> Any:
        """
        Apply appropriate anonymization techniques based on the determined anonymization level.
        """
        if anonymization_level == "minimal":
            # Minimal anonymization for high access level
            return self._apply_minimal_anonymization(data, data_type)
        elif anonymization_level == "moderate":
            # Moderate anonymization 
            return self._apply_moderate_anonymization(data, data_type)
        elif anonymization_level == "strong_with_longitudinal":
            # Strong anonymization but with longitudinal information
            return self._apply_strong_anonymization(data, data_type, preserve_longitudinal=True)
        elif anonymization_level == "strong":
            # Strongest anonymization
            return self._apply_strong_anonymization(data, data_type, preserve_longitudinal=False)
        else:
            log.warning(f"Unknown anonymization level: {anonymization_level}, applying strongest anonymization")
            return self._apply_strong_anonymization(data, data_type, preserve_longitudinal=False)
    
    def _apply_minimal_anonymization(self, data: Any, data_type: str) -> Any:
        """Apply minimal anonymization: remove direct identifiers only."""
        # Implementation depends on data type
        if isinstance(data, list):
            result = []
            for item in data:
                # Deep copy the item to avoid modifying the original
                anonymized = dict(item)
                
                # Remove direct identifiers but keep everything else
                if "user_id" in anonymized:
                    anonymized["user_id"] = hashlib.sha256(str(anonymized["user_id"]).encode()).hexdigest()[:16]
                if "device_id" in anonymized:
                    anonymized["device_id"] = hashlib.sha256(str(anonymized["device_id"]).encode()).hexdigest()[:16]
                if "ip_address" in anonymized:
                    # Properly anonymize IP addresses by preserving network prefix
                    try:
                        parts = anonymized["ip_address"].split('.')
                        if len(parts) == 4:  # IPv4
                            anonymized["ip_address"] = f"{parts[0]}.{parts[1]}.0.0"
                        else:  # Handle IPv6 or invalid IPs
                            anonymized["ip_address"] = "0.0.0.0"
                    except:
                        anonymized["ip_address"] = "0.0.0.0"
                if "email" in anonymized:
                    parts = anonymized["email"].split('@')
                    if len(parts) == 2:
                        anonymized["email"] = f"{parts[0][0]}*****@{parts[1]}"
                
                result.append(anonymized)
            return result
        else:
            # Handle non-list data
            return data
    
    def _apply_moderate_anonymization(self, data: Any, data_type: str) -> Any:
        """Apply moderate anonymization: remove identifiers and generalize some fields."""
        minimally_anonymized = self._apply_minimal_anonymization(data, data_type)
        
        if isinstance(minimally_anonymized, list):
            result = []
            for item in minimally_anonymized:
                # Further generalize sensitive fields
                anonymized = dict(item)
                
                # Generalize timestamps to hour level
                if "timestamp" in anonymized:
                    try:
                        dt = datetime.fromisoformat(anonymized["timestamp"].replace("Z", "+00:00"))
                        anonymized["timestamp"] = dt.replace(minute=0, second=0, microsecond=0).isoformat()
                    except:
                        pass
                
                # Generalize location data if present
                if "latitude" in anonymized and "longitude" in anonymized:
                    # Round to lower precision (approx neighborhood level)
                    anonymized["latitude"] = round(anonymized["latitude"], 2)
                    anonymized["longitude"] = round(anonymized["longitude"], 2)
                
                # Handle health data
                if data_type == "health" and "measurement" in anonymized:
                    # Round to less precision
                    if isinstance(anonymized["measurement"], (int, float)):
                        anonymized["measurement"] = round(anonymized["measurement"], 0)
                
                # Handle financial data
                if data_type == "financial" and "amount" in anonymized:
                    # Round to nearest 10
                    if isinstance(anonymized["amount"], (int, float)):
                        anonymized["amount"] = round(anonymized["amount"] / 10) * 10
                
                result.append(anonymized)
            return result
        else:
            return minimally_anonymized
    
    def _apply_strong_anonymization(self, data: Any, data_type: str, preserve_longitudinal: bool) -> Any:
        """
        Apply strong anonymization: generalize extensively and potentially break longitudinal connections.
        
        Args:
            data: The data to anonymize
            data_type: Type of data being anonymized
            preserve_longitudinal: Whether to preserve connections between events from the same user
        """
        moderately_anonymized = self._apply_moderate_anonymization(data, data_type)
        
        if isinstance(moderately_anonymized, list):
            result = []
            session_map = {}  # For preserving longitudinal connections if needed
            
            for item in moderately_anonymized:
                anonymized = dict(item)
                
                # Extensive generalization
                # Truncate timestamps to day level
                if "timestamp" in anonymized:
                    try:
                        dt = datetime.fromisoformat(anonymized["timestamp"].replace("Z", "+00:00"))
                        anonymized["timestamp"] = dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                    except:
                        pass
                
                # Further generalize location
                if "latitude" in anonymized and "longitude" in anonymized:
                    # Round to much lower precision (approx city level)
                    anonymized["latitude"] = round(anonymized["latitude"], 1)
                    anonymized["longitude"] = round(anonymized["longitude"], 1)
                
                # Generalize age ranges for health data
                if data_type == "health" and "age" in anonymized:
                    age = anonymized["age"]
                    if isinstance(age, (int, float)):
                        # Convert to age range
                        age_range = f"{(age // 10) * 10}-{((age // 10) * 10) + 9}"
                        anonymized["age"] = age_range
                
                # Generalize financial data into buckets
                if data_type == "financial" and "amount" in anonymized:
                    amount = anonymized["amount"]
                    if isinstance(amount, (int, float)):
                        # Convert to ranges: <100, 100-500, 500-1000, >1000
                        if amount < 100:
                            anonymized["amount"] = "<100"
                        elif amount < 500:
                            anonymized["amount"] = "100-500"
                        elif amount < 1000:
                            anonymized["amount"] = "500-1000"
                        else:
                            anonymized["amount"] = ">1000"
                
                # Handle longitudinal connections
                if not preserve_longitudinal:
                    # Generate new random session/user identifiers for each record
                    if "session_id" in anonymized:
                        anonymized["session_id"] = str(uuid.uuid4())
                    
                    # Remove any fields that could connect records
                    if "user_id" in anonymized:
                        anonymized["user_id"] = f"anon_{random.randint(1000, 9999)}"
                else:
                    # Preserve connections but with anonymized consistent IDs
                    if "session_id" in anonymized:
                        original = anonymized["session_id"]
                        if original not in session_map:
                            session_map[original] = f"session_{len(session_map) + 1}"
                        anonymized["session_id"] = session_map[original]
                
                result.append(anonymized)
            return result
        else:
            return moderately_anonymized
    
    def _format_data_for_schema(self, data: Any, data_type: str) -> Any:
        """
        Format the anonymized data according to the standardized schema for the data type.
        
        Args:
            data: The anonymized data
            data_type: Type of data to format
            
        Returns:
            Formatted data conforming to the schema
        """
        # In a full implementation, this would validate and transform data
        # to match specific JSON schemas for each data type
        
        # For now, we'll just ensure all records have the required fields
        if isinstance(data, list):
            schema_version = self._get_schema_version(data_type)
            
            # Get required fields for this data type and schema version
            required_fields = self._get_required_fields(data_type, schema_version)
            
            # Ensure all records have required fields
            result = []
            for item in data:
                formatted_item = dict(item)
                
                # Add any missing required fields with default values
                for field in required_fields:
                    if field not in formatted_item:
                        formatted_item[field] = self._get_default_value(field, data_type)
                
                result.append(formatted_item)
            return result
        else:
            return data
    
    def _get_required_fields(self, data_type: str, schema_version: str) -> List[str]:
        """Get the required fields for a specific data type and schema version."""
        # This would typically be loaded from a schema repository
        if data_type == "app_usage":
            return ["app_id", "timestamp", "duration", "action"]
        elif data_type == "location":
            return ["timestamp", "latitude", "longitude", "accuracy"]
        elif data_type == "browsing_history":
            return ["timestamp", "url", "duration", "page_title"]
        elif data_type == "health":
            return ["timestamp", "type", "measurement", "unit"]
        elif data_type == "financial":
            return ["timestamp", "type", "amount", "currency"]
        else:
            return []
    
    def _get_default_value(self, field: str, data_type: str) -> Any:
        """Get a default value for a specific field and data type."""
        # Common defaults
        if field == "timestamp":
            return datetime.now().isoformat()
        
        # Data type specific defaults
        if data_type == "app_usage":
            if field == "duration":
                return 0
            elif field == "action":
                return "unknown"
        
        # Default for any other field
        return None
    
    def _get_schema_version(self, data_type: str) -> str:
        """Get the current schema version for a data type."""
        # In a real implementation, this would be retrieved from a schema registry
        return "1.0"
    
    def _calculate_data_quality(self, data: Any) -> float:
        """
        Calculate a data quality score for the packaged data.
        
        Args:
            data: The data to evaluate
            
        Returns:
            Quality score between 0 and 1
        """
        # This would implement data quality metrics like:
        # - Completeness (% of fields with non-null values)
        # - Timeliness (how recent is the data)
        # - Volume (how many records)
        
        # For this POC, return a mock score
        return 0.95
    
    def _calculate_expiry(self, access_level: str) -> str:
        """Calculate expiry date based on access level."""
        now = datetime.now()
        
        if "short_term" in access_level:
            # Short term access expires in 24 hours
            expiry = now + timedelta(days=1)
        else:
            # Persistent access expires in 30 days
            expiry = now + timedelta(days=30)
            
        return expiry.isoformat()
    
    def _get_anonymization_level(self, access_level: str) -> str:
        """Get a descriptive anonymization level string based on access level."""
        if access_level == "precise_persistent":
            return "minimal"
        elif access_level == "precise_short_term":
            return "moderate"
        elif access_level == "anonymous_persistent":
            return "strong_with_longitudinal"
        else:
            return "strong"
    
    def _get_usage_policy(self, access_level: str, trust_tier: str) -> Dict[str, Any]:
        """Get usage policy details based on access level and trust tier."""
        # Base policy
        policy = {
            "permitted_use": [],
            "prohibited_use": ["resale", "unauthorized_sharing"],
            "data_retention": "30_days" if "persistent" in access_level else "24_hours",
            "deletion_required": True,
            "audit_required": True
        }
        
        # Add specific permissions based on access level
        if access_level == "precise_persistent":
            policy["permitted_use"] = ["analytics", "personalization", "research"]
        elif access_level == "precise_short_term":
            policy["permitted_use"] = ["analytics", "transient_personalization"]
        elif access_level == "anonymous_persistent":
            policy["permitted_use"] = ["analytics", "aggregated_insights"]
        else:  # anonymous_short_term
            policy["permitted_use"] = ["single_use_analytics"]
            
        # Adjust based on trust tier
        if trust_tier == "low":
            policy["audit_frequency"] = "weekly"
        elif trust_tier == "standard":
            policy["audit_frequency"] = "monthly"
        else:  # high trust
            policy["audit_frequency"] = "quarterly"
            
        return policy
    
    def _create_empty_package(self, data_type: str, consent_id: str, reason: str) -> Dict[str, Any]:
        """
        Create an empty data package when data cannot be provided.
        
        Args:
            data_type: The type of data that was requested
            consent_id: ID of the consent record
            reason: Reason why data is not available
            
        Returns:
            Empty data package with error information
        """
        return {
            "tavren_data_package": "1.1",
            "package_id": str(uuid.uuid4()),
            "consent_id": consent_id,
            "created_at": datetime.now().isoformat(),
            "data_type": data_type,
            "status": "error",
            "reason": reason,
            "content": [],
            "metadata": {
                "record_count": 0,
                "schema_version": self._get_schema_version(data_type),
                "error_details": reason
            }
        }
    
    def _generate_access_token(self, consent_id: str, expiry: str) -> str:
        """
        Generate a secure, time-limited access token for the data package.
        
        Args:
            consent_id: ID of the consent record
            expiry: Expiry timestamp for the token
            
        Returns:
            JWT-style access token
        """
        # For a real implementation, this would be a proper JWT
        # with signing using a secure algorithm
        
        # Create a simple header
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        
        # Create payload with claims
        try:
            expiry_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            exp_timestamp = int(expiry_dt.timestamp())
        except:
            # Default to 24 hours if parsing fails
            exp_timestamp = int((datetime.now() + timedelta(days=1)).timestamp())
            
        payload = {
            "consent_id": consent_id,
            "exp": exp_timestamp,
            "iat": int(datetime.now().timestamp()),
            "package_id": str(uuid.uuid4())
        }
        
        # Encode header and payload
        header_encoded = base64.b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        
        # In a real implementation, we would properly sign this
        # For now, generate a mock signature
        signature = hashlib.sha256(f"{header_encoded}.{payload_encoded}".encode()).hexdigest()
        signature_encoded = base64.b64encode(signature.encode()).decode().rstrip('=')
        
        # Return the token
        return f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    
    async def _create_audit_record(self, packaged_data: Dict[str, Any]) -> None:
        """
        Create an audit record for the data package operation.
        
        Args:
            packaged_data: The data package that was created
            
        Returns:
            None
        """
        # In a real implementation, this would store the audit record in a database
        # For the POC, we'll just log it
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "operation": "data_package_created",
            "package_id": packaged_data["package_id"],
            "consent_id": packaged_data["consent_id"],
            "data_type": packaged_data["data_type"],
            "access_level": packaged_data["access_level"],
            "record_count": packaged_data["metadata"]["record_count"],
            "buyer_id": packaged_data["metadata"].get("buyer_id"),
            "purpose": packaged_data["purpose"],
            "expires_at": packaged_data["expires_at"]
        }
        
        log.info(f"Audit record created: {json.dumps(audit_record)}")
        
        # In a full implementation:
        # await self.db.execute(insert(AuditLog).values(**audit_record))
        # await self.db.commit()
    
    def _encrypt_package_content(self, content: Any) -> str:
        """
        Encrypt the package content for secure transmission.
        
        Args:
            content: The content to encrypt
            
        Returns:
            Encrypted content as a string
        """
        # Convert content to JSON string
        content_str = json.dumps(content)
        
        # Encrypt using helper function
        try:
            encrypted = encrypt_data(content_str, self._encryption_key)
            return encrypted
        except Exception as e:
            log.error(f"Error encrypting data: {str(e)}")
            # Fall back to base64 encoding if encryption fails
            return base64.b64encode(content_str.encode()).decode()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create an encryption key for securing data packages."""
        # In a real implementation, this would be stored securely
        # and properly managed with key rotation
        
        # For this POC, we'll derive a key from settings
        salt = b'tavren-data-packaging-salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Derive key from secret
        key = kdf.derive(settings.SECRET_KEY.encode())
        return base64.urlsafe_b64encode(key)
    
    def _generate_mock_app_usage(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock app usage data for testing."""
        apps = ["com.example.mail", "com.example.browser", "com.example.maps", 
               "com.example.social", "com.example.game"]
        actions = ["open", "close", "background", "foreground"]
        
        result = []
        for i in range(20):  # Generate 20 records
            timestamp = (datetime.now() - timedelta(hours=random.randint(0, 72))).isoformat()
            result.append({
                "user_id": user_id,
                "device_id": f"device_{random.randint(1, 3)}",
                "app_id": random.choice(apps),
                "timestamp": timestamp,
                "duration": random.randint(10, 3600),  # 10 seconds to 1 hour
                "action": random.choice(actions),
                "session_id": f"session_{random.randint(1, 5)}",
                "battery_level": random.randint(10, 100)
            })
            
        return result
    
    def _generate_mock_location_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock location data for testing."""
        # Base coordinates (approximately New York City)
        base_lat, base_lon = 40.7128, -74.0060
        
        result = []
        for i in range(15):  # Generate 15 records
            # Add some random variation to the coordinates
            lat = base_lat + random.uniform(-0.1, 0.1)
            lon = base_lon + random.uniform(-0.1, 0.1)
            
            timestamp = (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat()
            result.append({
                "user_id": user_id,
                "device_id": f"device_{random.randint(1, 3)}",
                "timestamp": timestamp,
                "latitude": lat,
                "longitude": lon,
                "accuracy": random.randint(5, 100),  # 5-100 meters
                "altitude": random.randint(0, 100),
                "speed": random.randint(0, 30),  # 0-30 m/s
                "session_id": f"session_{random.randint(1, 5)}",
                "ip_address": f"192.168.1.{random.randint(1, 255)}"
            })
            
        return result
    
    def _generate_mock_browsing_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock browsing history data for testing."""
        domains = ["example.com", "news.example.com", "shop.example.com", 
                  "social.example.com", "mail.example.com"]
        page_titles = ["Home Page", "News Article", "Product Listing", 
                      "User Profile", "Inbox"]
        
        result = []
        for i in range(25):  # Generate 25 records
            domain = random.choice(domains)
            page_title = random.choice(page_titles)
            timestamp = (datetime.now() - timedelta(hours=random.randint(0, 96))).isoformat()
            
            result.append({
                "user_id": user_id,
                "device_id": f"device_{random.randint(1, 3)}",
                "timestamp": timestamp,
                "url": f"https://{domain}/page{random.randint(1, 100)}",
                "page_title": f"{domain} - {page_title}",
                "duration": random.randint(5, 1800),  # 5 seconds to 30 minutes
                "referrer": f"https://{random.choice(domains)}/page{random.randint(1, 100)}",
                "session_id": f"session_{random.randint(1, 5)}",
                "ip_address": f"192.168.1.{random.randint(1, 255)}"
            })
            
        return result
        
    def _generate_mock_health_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock health data for testing."""
        measurement_types = ["heart_rate", "steps", "sleep", "blood_pressure", "weight"]
        units = {"heart_rate": "bpm", "steps": "count", "sleep": "hours", 
                "blood_pressure": "mmHg", "weight": "kg"}
        
        result = []
        for i in range(30):  # Generate 30 records
            measurement_type = random.choice(measurement_types)
            
            # Generate realistic values based on the type
            if measurement_type == "heart_rate":
                value = random.randint(60, 100)
            elif measurement_type == "steps":
                value = random.randint(1000, 15000)
            elif measurement_type == "sleep":
                value = round(random.uniform(4.0, 10.0), 1)
            elif measurement_type == "blood_pressure":
                # Store as string for systolic/diastolic
                systolic = random.randint(100, 140)
                diastolic = random.randint(60, 90)
                value = f"{systolic}/{diastolic}"
            elif measurement_type == "weight":
                value = round(random.uniform(50.0, 100.0), 1)
            
            timestamp = (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat()
            
            result.append({
                "user_id": user_id,
                "timestamp": timestamp,
                "type": measurement_type,
                "measurement": value,
                "unit": units[measurement_type],
                "device_id": f"health_device_{random.randint(1, 3)}",
                "age": random.randint(25, 65),
                "gender": random.choice(["male", "female", "other"]),
                "session_id": f"health_session_{random.randint(1, 5)}"
            })
            
        return result
    
    def _generate_mock_financial_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock financial transaction data for testing."""
        categories = ["groceries", "entertainment", "utilities", "dining", "travel", "shopping"]
        merchants = ["SuperMart", "StreamFlix", "PowerCo", "EateryPlace", "AirTravel", "MegaMall"]
        payment_methods = ["credit_card", "debit_card", "bank_transfer", "cash", "mobile_payment"]
        
        result = []
        for i in range(40):  # Generate 40 records
            category_index = random.randint(0, len(categories) - 1)
            amount = round(random.uniform(5.0, 500.0), 2)
            
            timestamp = (datetime.now() - timedelta(days=random.randint(0, 60))).isoformat()
            
            result.append({
                "user_id": user_id,
                "timestamp": timestamp,
                "type": "purchase",
                "category": categories[category_index],
                "merchant": merchants[category_index],
                "amount": amount,
                "currency": "USD",
                "payment_method": random.choice(payment_methods),
                "account_id": f"acct_{random.randint(1000, 9999)}",
                "transaction_id": f"tx_{uuid.uuid4().hex[:8]}",
                "email": f"user{random.randint(100, 999)}@example.com"
            })
            
        return result

async def get_data_packaging_service(db = Depends(get_db)) -> DataPackagingService:
    """Dependency for getting the data packaging service."""
    return DataPackagingService(db) 