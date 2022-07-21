from curses import raw
from urllib.parse import urlparse
import hashlib
import json
import os
import logging

from telemetry_orchestrator.server.models.metric import (
    MetricModel
)

from telemetry_orchestrator.server.models.ue_location import (
    UELocationModel
)

logger = logging.getLogger(__name__)

PROMETHEUS_URI = os.getenv("PROMETHEUS_URI")

NDAC_URI_GET = os.getenv("NDAC_URI_GET")

NDAC_URI_POST = os.getenv("NDAC_URI_POST")

KAFKA_ENDPOINT = os.getenv("KAFKA_ENDPOINT")

SITE_ID = os.getenv("SITE_ID")


def _getQueryLabels(expression: dict) -> str:
    """
    Print Prometheus labels to make them consumable
    by Prometheus REST API.
    """
    labels = []
    for label, value in expression.items():
        labels.append("{0}='{1}'".format(label, value))

    return ",".join(labels)


def _parseOperationSyntax(operation: str) -> str:
    """
    Parse syntax of the delimiter of a Prometheus operation when any condition 
    of a label has an empty value. (e.g., {image!=""} -> {image!=\"\"})
    """
    new_operation = ""
    for index in range(len(operation)):
        character = operation[index]
        if character == '"' and operation[index+1] == '"':
            new_operation = new_operation + "\"\""
        else:
            if not (character == '"' and operation[index-1] == '"'):
                new_operation = new_operation + character
        
    return new_operation


def config_metric_source(metric: MetricModel, metric_id: str) -> dict:
    """
    Builds configuration arguments for MetricSource application (NiFi)
    """

    # Get source Metric
    source_metric = ""
    if metric.operation:
        source_metric = metric.operation
        # source_metric = _parseOperationSyntax(metric.operation)
    else:
        source_metric = metric.metricname

    logger.info("Metric '{0}'.".format(source_metric))

    # Get source Prometheus
    source_prom_endpoint = str(PROMETHEUS_URI)

    # Build URL based on optional expression
    prometheus_request = ""
    if metric.labels:
        labels = _getQueryLabels(metric.labels)
        prometheus_request = (
            source_prom_endpoint +
            "?query=" + source_metric +
            "{" + labels + "}")
    else:
        prometheus_request = (source_prom_endpoint + "?query=" + source_metric)        

    # DEPRECATED:
    # Generation of topic ID from the hash composed of the metric along with 
    # its own tags
    # raw_topic_id = metric.metricname+labels
    # topic_id = hashlib.md5(raw_topic_id.encode("utf-8")).hexdigest()
    
    # Topic ID = Metric's Object ID within MongoDB
    topic_id = metric_id 

    # Collect variables for MetricSource
    # Sink Kafka topic
    sink_topic_name = str(SITE_ID)+"-"+metric.metricname+"-"+topic_id

    # Endpoint for sink Kafka broker
    sink_broker_url = str(KAFKA_ENDPOINT)

    arguments = {
        "interval": metric.interval,
        "prometheus_request": prometheus_request,
        "sink_broker_url": sink_broker_url,
        "sink_topic": sink_topic_name
    }
    return arguments


def config_ue_location_source(ue_location: UELocationModel, 
                              ue_location_id: str) -> dict:
    """
    Builds configuration arguments for NDACSource application (NiFi)
    """

    # Get source NDAC endpoints
    source_ndac_get_endpoint = str(NDAC_URI_GET) 
    source_ndac_post_endpoint = str(NDAC_URI_POST)        

    # DEPRECATED:
    # Generation of topic ID from the hash composed of the metric along with 
    # its own tags
    # raw_topic_id = metric.metricname+labels
    # topic_id = hashlib.md5(raw_topic_id.encode("utf-8")).hexdigest()
    
    # Topic ID = Metric's Object ID within MongoDB
    topic_id = ue_location_id 

    # Collect variables for MetricSource
    # Sink Kafka topics
    topic_icc_ids = "icc-ids"+"-"+topic_id
    topic_icc_info = "icc-info"+"-"+topic_id

    # Endpoint for sink Kafka broker
    sink_broker_url = str(KAFKA_ENDPOINT)

    arguments = {
        "interval": ue_location.interval,
        "ndac_get_url": source_ndac_get_endpoint,
        "ndac_post_url": source_ndac_post_endpoint,
        "sink_broker_url": sink_broker_url,
        "topic_icc_ids": topic_icc_ids,
        "topic_icc_info": topic_icc_info
    }
    return arguments


nifi_application_configs = {
    "MetricSource": config_metric_source,
    "MetricSourceYANG": config_metric_source,
    "NDACSource": config_ue_location_source
}
