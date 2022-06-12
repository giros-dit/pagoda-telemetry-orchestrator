from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MetricSchema(BaseModel):
    metricname: str = Field(...)
    labels: Dict[str, Any] = Field(...)
    interval: int = Field(...)
    description: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "metricname": "up",
                "labels": {'instance': 'node-exporter:9100', 'job': 'node'},
                "interval": 10000,
                "description": "UP metric",
            }
        }


class UpdateMetricModel(BaseModel):
    metricname: Optional[str]
    labels: Optional[Dict[str, Any]]
    interval: Optional[int]
    description: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "metricname": "up",
                "labels": {'instance': 'node-exporter:9100', 'job': 'node'},
                "interval": 10000,
                "description": "UP metric",
            }
        }


def ResponseModel(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {
        "error": error, 
        "code": code, 
        "message": message
    }