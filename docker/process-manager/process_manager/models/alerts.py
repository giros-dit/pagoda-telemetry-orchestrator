from typing import Any, Dict, Optional, List, Union

from enum import Enum

from pydantic import BaseModel, Field


class AlertModel(BaseModel):
    filename: str = Field(...)
    rulename: str = Field(...)
    alertname: str = Field(...)
    expr: str = Field(...)
    duration: str = Field(...)
    severity: str = Field(...)
    summary: str = Field(...)
    description: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "filename": "example",
                "rulename": "host",
                "alertname": "high_cpu",
                "expr": "node_load1 > 10.5",
                "duration": "2m",
                "severity": "critical",
                "summary": "Server CPU is under high load.",
                "description": 
                "Server CPU is under high load."
            }
        }


class ResponseModel(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any], str] = Field(...)
    code: int = Field(default=200)
    message: str = Field(...)  


class AddAlertResponseModel(ResponseModel):
    data: Dict[str, Any] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": {
                    "id": "62aad459fb672f7a0a80e0cf",
                    "filename": "example",
                    "rulename": "host",
                    "alertname": "high_cpu",
                    "expr": "node_load1 > 10.5",
                    "duration": "2m",
                    "severity": "critical",
                    "summary": "Server CPU is under high load",
                    "description": 
                        "Server CPU is under high load."
                },
                "code": 200,
                "message": "Alert added successfully."
            }
        }


class GetAlertResponseModel(ResponseModel):
    data: Dict[str, Any] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": {
                    "id": "62aad459fb672f7a0a80e0cf",
                    "filename": "example",
                    "rulename": "host",
                    "alertname": "high_cpu",
                    "expr": "node_load1 > 10.5",
                    "duration": "2m",
                    "severity": "critical",
                    "summary": "Server CPU is under high load",
                    "description": 
                        "Server CPU is under high load."
                },
                "code": 200,
                "message": "Alert data retrieved successfully."
            }
        }


class GetAlertsResponseModel(ResponseModel):
    data: List[Dict[str, Any]] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": [
                    {
                        "id": "62aad459fb672f7a0a80e0cf",
                        "filename": "example1",
                        "rulename": "host",
                        "alertname": "high_cpu",
                        "expr": "node_load1 > 10.5",
                        "duration": "2m",
                        "severity": "critical",
                        "summary": "Server CPU is under high load",
                        "description": 
                            "Server CPU is under high load."
                    },
                    {
                        "id": "62aad459fb672f7a0a80e0cf",
                        "filename": "example2",
                        "rulename": "host",
                        "alertname": "high_cpu",
                        "expr": "node_load1 > 9.5",
                        "duration": "2m",
                        "severity": "critical",
                        "summary": "Server CPU is under high load",
                        "description": 
                            "Server CPU is under high load."
                    }
                ],
                "code": 200,
                "message": "Alerts data retrieved successfully."
            }
        }

class DeleteAlertResponseModel(ResponseModel):
    data: str = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": "Alert with ID 62aad459fb672f7a0a80e0cf removed.",
                "code": 200,
                "message": "Alert deleted successfully."
            }
        } 