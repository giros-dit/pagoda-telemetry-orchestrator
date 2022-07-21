from typing import Any, Dict, Optional, List, Union

from pydantic import BaseModel, Field
from datetime import datetime


class UELocationModel(BaseModel):
    interval: int = Field(...)
    description: Optional[str] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "interval": 10000,
                "description": "UE location activation."
            }
        }


class UpdateUELocationModel(BaseModel):
    interval: int = Field(...)
    description: Optional[str] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "interval": 15000,
                "description": "UE location information."
            }
        }


class ResponseModel(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any], str] = Field(...)
    code: int = Field(default=200)
    message: str = Field(...)  


class AddUELocationResponseModel(ResponseModel):
    data: Dict[str, Any] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": {
                    "id": "62d8f4a4dc17fe14a0ddc4a5",
                    "interval": 10000,
                    "description": "UE location information."
                },
                "code": 200,
                "message": "UE location activated successfully."
            }
        }


class GetUELocationResponseModel(ResponseModel):
    data: Dict[str, Any] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": {
                    "id": "62d8f4a4dc17fe14a0ddc4a5",
                    "interval": 10000,
                    "description": "UE location information."
                },
                "code": 200,
                "message": "UE location interval retrieved successfully."
            }
        }


class GetUELocationsResponseModel(ResponseModel):
    data: List[Dict[str, Any]] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": [{
                    "id": "62d8f4a4dc17fe14a0ddc4a5",
                    "interval": 10000,
                    "description": "UE location information."
                }],
                "code": 200,
                "message": "UE location interval retrieved successfully."
            }
        }


class UpdateUELocationResponseModel(ResponseModel):
    data: str = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": "UE location interval updated.",
                "code": 200,
                "message": "UE location interval updated successfully."
            }
        }    


class DeleteUELocationResponseModel(ResponseModel):
    data: str = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": "UE location desactivated.",
                "code": 200,
                "message": "UE location desactivated successfully."
            }
        } 