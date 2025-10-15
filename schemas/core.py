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

class StandardResponse(APIResponse[Any]):
    """
    Standard API response with flexible data type.
    
    Use this for endpoints that return varying data types.
    Accepts lists, objects, empty dicts, etc.
    
    Example:
    return StandardResponse(data=[users], message="Users retrieved")
    return StandardResponse(data={}, message="No data found")
    """
    pass

class EmptyDataResponse(APIResponse[dict]):
    """
    API response specifically for empty data scenarios.
    
    Use this when you know the response will always have empty data {}.
    Provides better type hints than StandardResponse for empty responses.
    
    Example:
    return EmptyDataResponse(data={}, message="Operation completed")
    """
    pass
