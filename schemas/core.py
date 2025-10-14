from pydantic import BaseModel
from typing import TypeVar, Generic, Any

# Generic type for data
DataType = TypeVar('DataType')

class APIResponse(BaseModel, Generic[DataType]):
    """
    Generic API response model that follows the project's standard format.
    
    Format:
    {
        "data": { /* payload object, may be empty {} */ },
        "message": "A short message"
    }
    """
    data: DataType
    message: str

# Convenience alias for responses with any data type
class StandardResponse(APIResponse[Any]):
    """Standard response with flexible data type"""
    pass

# Common response for empty data
class EmptyDataResponse(APIResponse[dict]):
    """Response with empty data object"""
    pass
