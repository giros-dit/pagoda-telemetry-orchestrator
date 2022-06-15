from curses import raw
from urllib.parse import urlparse
import hashlib
import json
import os
import logging

from telemetry_orchestrator.server.models.metric import (
    MetricModel
)

logger = logging.getLogger(__name__)

PROMETHEUS_URI = os.getenv("PROMETHEUS_URI")

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


def config_metric_source(metric: MetricModel, metric_id: str) -> dict:
    """
    Builds configuration arguments for MetricSource application (NiFi)
    """

    # Get source Metric
    source_metric = metric.metricname

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

    # Endpoint for source Kafka broker
    sink_broker_url = str(KAFKA_ENDPOINT)

    arguments = {
        "interval": metric.interval,
        "prometheus_request": prometheus_request,
        "sink_broker_url": sink_broker_url,
        "sink_topic": sink_topic_name
    }
    return arguments


nifi_application_configs = {
    "MetricSource": config_metric_source,
    "MetricSourceYANG": config_metric_source
}
