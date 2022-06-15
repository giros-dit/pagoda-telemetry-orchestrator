from typing import Any, Dict, Optional, List, Union

from pydantic import BaseModel, Field


class MetricModel(BaseModel):
    metricname: str = Field(...)
    labels: Optional[Dict[str, Any]] = Field(...)
    interval: int = Field(...)
    description: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "metricname": "up",
                "labels": {'instance': 'node-exporter:9100', 'job': 'node'},
                "interval": 10000,
                "description": "UP metric within node-exporter instance",
            }
        }


class UpdateMetricModel(BaseModel):
    labels: Optional[Dict[str, Any]]
    interval: Optional[int]
    description: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "labels": {'instance': 'localhost:9090', 'job': 'prometheus'},
                "interval": 5000,
                "description": "UP metric within Prometheus instance",
            }
        }


class ResponseModel(BaseModel):
    data: Union[List[Dict[str, Any]],Dict[str, Any], str] = Field(...)
    code: int = Field(default=200)
    message: str = Field(...)  