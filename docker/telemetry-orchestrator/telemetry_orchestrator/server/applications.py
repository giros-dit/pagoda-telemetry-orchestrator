from curses import raw
import json
import logging
from urllib.parse import urlparse
import hashlib


from telemetry_orchestrator.server.models.metric import (
    ErrorResponseModel,
    ResponseModel,
    MetricSchema,
    UpdateMetricModel,
)
logger = logging.getLogger(__name__)


def _getQueryLabels(expression: dict) -> str:
    """
    Print Prometheus labels to make them consumable
    by Prometheus REST API.
    """
    labels = []
    for label, value in expression.items():
        labels.append("{0}='{1}'".format(label, value))

    return ",".join(labels)


def config_metric_source(metric: MetricSchema) -> dict:
    """
    Builds configuration arguments for MetricSource application (NiFi)
    """

    # Get source Metric
    source_metric = metric.metricname

    # Get source Prometheus
    source_prom_endpoint = "http://prometheus:9090/api/v1/query"

    # Build URL based on optional expression
    prometheus_request = ""
    labels = _getQueryLabels(metric.labels)
    prometheus_request = (
         source_prom_endpoint +
        "?query=" + source_metric +
        "{" + labels + "}")

    # Generation of topic ID from the metric hash and its own labels
    raw_topic_id = metric.metricname+labels
    topic_id = hashlib.md5(raw_topic_id.encode("utf-8")).hexdigest()

    # Collect variables for MetricSource
    # Sink Kafka topic
    sink_topic_name = metric.metricname+"-"+topic_id
    print(sink_topic_name)
    # Endpoint for source Kafka broker
    sink_broker_url = "kafka:9092"

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
