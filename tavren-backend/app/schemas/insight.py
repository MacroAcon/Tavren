from enum import Enum
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator
import pandas as pd
import json
import io

from app.utils.insight_processor import QueryType, PrivacyMethod

class DataFormat(str, Enum):
    """Enumeration of supported data formats."""
    CSV = "csv"
    JSON = "json"
    FILENAME = "filename"

class InsightRequest(BaseModel):
    """
    Schema for insight request payload.
    
    Attributes:
        data: Dataset as CSV string, list of dictionaries, or filename
        query_type: Type of insight query to process
        pet_method: Privacy-enhancing technology method to use
        epsilon: Privacy parameter for differential privacy (required if pet_method is "dp")
        data_format: Format of the provided data
    """
    data: str = Field(..., description="Dataset as CSV string, JSON string, or filename")
    query_type: QueryType = Field(..., description="Type of insight query to process")
    pet_method: PrivacyMethod = Field(..., description="Privacy-enhancing technology method to use")
    epsilon: Optional[float] = Field(None, description="Privacy parameter for differential privacy")
    data_format: DataFormat = Field(DataFormat.CSV, description="Format of the provided data")

    @validator('epsilon')
    def validate_epsilon(cls, v, values):
        """Validate that epsilon is provided if DP method is selected."""
        if values.get('pet_method') == PrivacyMethod.DP and v is None:
            raise ValueError("Epsilon is required when using differential privacy")
        return v

    def process_data(self) -> Any:
        """Process the data into the appropriate format for the insight processor."""
        if self.data_format == DataFormat.CSV:
            # Convert CSV string to DataFrame
            return pd.read_csv(io.StringIO(self.data))
        elif self.data_format == DataFormat.JSON:
            # Convert JSON string to list or DataFrame based on PET method
            if self.pet_method == PrivacyMethod.DP:
                # For DP, convert to DataFrame
                return pd.DataFrame(json.loads(self.data))
            else:
                # For SMPC, keep as list of party data
                return json.loads(self.data)
        elif self.data_format == DataFormat.FILENAME:
            # Process file based on extension
            if self.data.endswith('.csv'):
                return pd.read_csv(self.data)
            elif self.data.endswith('.json'):
                with open(self.data) as f:
                    data = json.load(f)
                    if self.pet_method == PrivacyMethod.DP:
                        return pd.DataFrame(data)
                    return data
            else:
                raise ValueError(f"Unsupported file format: {self.data}")
        
        return None

class InsightResponse(BaseModel):
    """
    Schema for insight response.
    
    Attributes:
        processed_result: Result of the insight processing
        privacy_method_used: Privacy method that was used
        metadata: Additional information about the processing
    """
    processed_result: Dict[str, Any] = Field(..., description="Result of the insight processing")
    privacy_method_used: PrivacyMethod = Field(..., description="Privacy method that was used")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata about the processing")

class ApiInfoResponse(BaseModel):
    """
    Schema for API info response.
    
    Attributes:
        supported_query_types: List of supported query types
        supported_privacy_methods: List of supported privacy methods
        example_payload: Example payload structure
    """
    supported_query_types: List[str] = Field(..., description="List of supported query types")
    supported_privacy_methods: List[str] = Field(..., description="List of supported privacy methods")
    example_payload: Dict[str, Any] = Field(..., description="Example payload structure") 