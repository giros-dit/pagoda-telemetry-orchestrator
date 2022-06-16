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
                "metricname": "node_network_transmit_packets_total",
                "labels": {
                    'job': 'node'
                },
                "interval": 10000,
                "description": 
                "Packets transmitted through network interfaces."
            }
        }


class UpdateMetricModel(BaseModel):
    labels: Optional[Dict[str, Any]]
    interval: Optional[int]
    description: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "labels": {
                    'device': 'eth0',
                    'instance': 'node-exporter:9100', 
                    'job': 'node'
                },
                "interval": 5000
            }
        }


class ResponseModel(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any], str] = Field(...)
    code: int = Field(default=200)
    message: str = Field(...)  


class AddMetricResponseModel(ResponseModel):
    data: Dict[str, Any] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": {
                    "id": "62aad459fb672f7a0a80e0cf",
                    "metricname": "node_network_transmit_packets_total",
                    "labels": {
                        "job": "node"
                    },
                    "interval": 10000,
                    "description": 
                    "Packets transmitted through network interfaces."
                },
                "code": 200,
                "message": "Metric added successfully."
            }
        }


class GetMetricResponseModel(ResponseModel):
    data: Dict[str, Any] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": {
                    "id": "62aad459fb672f7a0a80e0cf",
                    "metricname": "node_network_transmit_packets_total",
                    "labels": {
                        "instance": "node-exporter:9100",
                        "job": "node"
                    },
                    "interval": 5000,
                    "description": 
                    "Packets transmitted through network interfaces."
                },
                "code": 200,
                "message": "Metric data retrieved successfully."
            }
        }


class GetMetricsResponseModel(ResponseModel):
    data: List[Dict[str, Any]] = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": [
                    {
                        "id": "62aad459fb672f7a0a80e0cf",
                        "metricname": "up",
                        "labels": {
                            "instance": "node-exporter:9100",
                            "job": "node"
                        },
                        "interval": 10000,
                        "description": 
                        "The node-exporter instance is up."
                    },
                    {
                        "id": "62aad9fa0ecf10140cd50534",
                        "metricname": "node_network_transmit_packets_total",
                        "labels": {
                            "instance": "node-exporter:9100",
                            "job": "node"
                        },
                        "interval": 5000,
                        "description": 
                        "Packets transmitted through network interfaces."
                    }
                ],
                "code": 200,
                "message": "Metrics data retrieved successfully."
            }
        }


class UpdateMetricResponseModel(ResponseModel):
    data: str = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": "Metric with ID 62aad459fb672f7a0a80e0cf updated.",
                "code": 200,
                "message": "Metric data updated successfully."
            }
        }    


class DeleteMetricResponseModel(ResponseModel):
    data: str = Field(...) 

    class Config:
        schema_extra = { 
            "example": {
                "data": "Metric with ID 62aad459fb672f7a0a80e0cf removed.",
                "code": 200,
                "message": "Metric deleted successfully."
            }
        } 