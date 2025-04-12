import logging
import json
import uuid
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

# Get logger
log = logging.getLogger("app")

class DataPackagingService:
    """
    Service for packaging user data according to agent requests and consent preferences.
    Responsible for:
    - Retrieving user data based on data type
    - Applying appropriate anonymization based on access level
    - Formatting data according to MCP specifications
    - Generating secure access tokens/links
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def package_data(self, user_id: str, data_type: str, access_level: str, 
                          consent_id: str, purpose: str) -> Dict[str, Any]:
        """
        Main method to retrieve, anonymize, and package data based on request parameters.
        
        Args:
            user_id: ID of the user whose data is being requested
            data_type: Type of data being requested (e.g., "app_usage", "location")
            access_level: Access level requested (e.g., "anonymous_short_term")
            consent_id: ID of the consent record for this data exchange
            purpose: Purpose for data use as specified in MCP context
            
        Returns:
            Dict containing the packaged data with appropriate metadata
        """
        log.info(f"Packaging {data_type} data for user {user_id} at {access_level} access level")
        
        # 1. Retrieve raw data
        raw_data = await self._retrieve_data(user_id, data_type)
        if not raw_data:
            log.warning(f"No {data_type} data found for user {user_id}")
            return self._create_empty_package(data_type, consent_id, "Data not available")
        
        # 2. Apply anonymization based on access level
        anonymized_data = self._anonymize_data(raw_data, data_type, access_level)
        
        # 3. Format according to MCP specs with appropriate metadata
        packaged_data = {
            "tavren_data_package": "1.0",
            "package_id": str(uuid.uuid4()),
            "consent_id": consent_id,
            "created_at": datetime.now().isoformat(),
            "data_type": data_type,
            "access_level": access_level,
            "purpose": purpose,
            "expires_at": self._calculate_expiry(access_level),
            "anonymization_level": self._get_anonymization_level(access_level),
            "content": anonymized_data,
            "metadata": {
                "record_count": len(anonymized_data) if isinstance(anonymized_data, list) else 1,
                "schema_version": "1.0",
                "data_quality_score": 0.95,  # Mock value
                "mcp_context": {
                    "purpose": purpose,
                    "usage_policy": self._get_usage_policy(access_level)
                }
            }
        }
        
        log.info(f"Successfully packaged {data_type} data (ID: {packaged_data['package_id']})")
        return packaged_data
    
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
        else:
            log.warning(f"Unknown data type: {data_type}")
            return None
    
    def _anonymize_data(self, data: Any, data_type: str, access_level: str) -> Any:
        """
        Apply appropriate anonymization techniques based on access level.
        """
        if access_level == "precise_persistent":
            # Minimal anonymization for high access level
            return self._apply_minimal_anonymization(data, data_type)
        elif access_level == "precise_short_term":
            # Moderate anonymization 
            return self._apply_moderate_anonymization(data, data_type)
        elif access_level == "anonymous_persistent":
            # Strong anonymization but with longitudinal information
            return self._apply_strong_anonymization(data, data_type, preserve_longitudinal=True)
        elif access_level == "anonymous_short_term":
            # Strongest anonymization
            return self._apply_strong_anonymization(data, data_type, preserve_longitudinal=False)
        else:
            log.warning(f"Unknown access level: {access_level}, applying strongest anonymization")
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
                    anonymized["ip_address"] = "xxx.xxx.xxx.xxx"
                
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
    
    def _get_usage_policy(self, access_level: str) -> Dict[str, Any]:
        """Get usage policy details based on access level."""
        if "short_term" in access_level:
            return {
                "retention": "24_hours",
                "sharing": "prohibited",
                "reuse": "single_purpose"
            }
        else:
            return {
                "retention": "30_days",
                "sharing": "with_consent",
                "reuse": "related_purpose"
            }
    
    def _create_empty_package(self, data_type: str, consent_id: str, reason: str) -> Dict[str, Any]:
        """Create an empty data package when data is not available."""
        return {
            "tavren_data_package": "1.0",
            "package_id": str(uuid.uuid4()),
            "consent_id": consent_id,
            "created_at": datetime.now().isoformat(),
            "data_type": data_type,
            "content": [],
            "status": "empty",
            "reason": reason,
            "metadata": {
                "record_count": 0,
                "schema_version": "1.0"
            }
        }
    
    # Mock data generation methods
    def _generate_mock_app_usage(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock app usage data for demo purposes."""
        apps = ["social_media_app", "productivity_tool", "news_reader", "messaging_app", "finance_app"]
        actions = ["open", "close", "background", "foreground", "interaction"]
        
        result = []
        # Generate 20 random app usage events
        for i in range(20):
            # Create events over the past week
            event_time = datetime.now() - timedelta(days=random.randint(0, 7), 
                                                 hours=random.randint(0, 23),
                                                 minutes=random.randint(0, 59))
            
            result.append({
                "user_id": user_id,
                "session_id": f"session_{random.randint(1, 5)}",  # Simulate a few sessions
                "app_id": random.choice(apps),
                "action": random.choice(actions),
                "duration_seconds": random.randint(10, 3600) if "close" in actions else None,
                "timestamp": event_time.isoformat(),
                "device_type": random.choice(["mobile", "desktop", "tablet"]),
                "os_version": f"{random.randint(10, 15)}.{random.randint(0, 9)}",
                "ip_address": f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
            })
            
        return result
    
    def _generate_mock_location_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock location data for demo purposes."""
        # Base coordinates (approximately San Francisco)
        base_lat, base_lng = 37.7749, -122.4194
        
        result = []
        # Generate 15 location points
        for i in range(15):
            # Create events over the past 3 days
            event_time = datetime.now() - timedelta(days=random.randint(0, 3), 
                                                 hours=random.randint(0, 23),
                                                 minutes=random.randint(0, 59))
            
            # Generate nearby coordinates
            lat = base_lat + (random.random() - 0.5) * 0.1  # +/- 0.05 degrees
            lng = base_lng + (random.random() - 0.5) * 0.1
            
            result.append({
                "user_id": user_id,
                "device_id": f"device_{random.randint(1, 3)}",
                "latitude": lat,
                "longitude": lng,
                "accuracy_meters": random.randint(5, 50),
                "timestamp": event_time.isoformat(),
                "speed_kph": random.randint(0, 50) if random.random() > 0.7 else 0,
                "altitude_meters": random.randint(0, 100),
                "location_source": random.choice(["gps", "network", "cell_tower", "wifi"]),
                "battery_level": random.randint(10, 100)
            })
            
        return result
    
    def _generate_mock_browsing_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate mock browsing history data for demo purposes."""
        domains = ["example.com", "news.com", "shopping.site", "social.network", "video.streaming", 
                  "mail.service", "search.engine", "blog.platform", "forum.site", "education.org"]
        
        categories = ["news", "shopping", "social", "entertainment", "productivity", 
                     "technology", "sports", "finance", "travel", "education"]
        
        result = []
        # Generate 25 browsing events
        for i in range(25):
            # Create events over the past 10 days
            event_time = datetime.now() - timedelta(days=random.randint(0, 10), 
                                                 hours=random.randint(0, 23),
                                                 minutes=random.randint(0, 59))
            
            domain = random.choice(domains)
            result.append({
                "user_id": user_id,
                "session_id": f"browsing_{random.randint(1, 8)}",
                "domain": domain,
                "url_path": f"/{random.choice(['index', 'article', 'product', 'profile', 'video', 'search'])}/{random.randint(1000, 9999)}",
                "timestamp": event_time.isoformat(),
                "duration_seconds": random.randint(5, 900),
                "category": random.choice(categories),
                "interaction_count": random.randint(0, 50),
                "referrer_domain": random.choice(domains) if random.random() > 0.3 else None,
                "device_type": random.choice(["mobile", "desktop", "tablet"]),
                "browser": random.choice(["chrome", "firefox", "safari", "edge"])
            })
            
        return result

# Factory function for dependency injection
async def get_data_packaging_service(db: AsyncSession) -> DataPackagingService:
    """Factory function for creating a DataPackagingService instance."""
    return DataPackagingService(db) 