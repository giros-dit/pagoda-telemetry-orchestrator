import logging

from telemetry_orchestrator.server.models.metric import (
    ErrorResponseModel,
    ResponseModel,
    MetricSchema,
    UpdateMetricModel,
)
from telemetry_orchestrator.server.nificlient import NiFiClient

from telemetry_orchestrator.server.applications import nifi_application_configs

logger = logging.getLogger(__name__)

def process_metric(metric: MetricSchema, metric_id: str, nifi: NiFiClient):
    """
    Process Metric
    """
    logger.info("Processing metric with name %s" % (
        metric.metricname))
    logger.info(
        "Instantiating new '{0}'...".format(metric.metricname))
    # Renew access token for NiFi API
    nifi.login()
    arguments = nifi_application_configs[
        "MetricSource"](metric, metric_id)
    nifi.instantiate_flow_from_metric(
        metric, metric_id, "MetricSource", arguments)

def reprocess_metric(metric: MetricSchema, metric_id: str, nifi: NiFiClient):
    """
    Reprocess Metric
    """
    logger.info("Reprocessing metric with name %s" % (
        metric.metricname))
    logger.info(
        "Updating '{0}'...".format(metric.metricname))
    # Renew access token for NiFi API
    nifi.login()
    arguments = nifi_application_configs[
        "MetricSource"](metric, metric_id)
    nifi.update_flow_from_metric(metric, metric_id, arguments)

def unprocess_metric(metric: MetricSchema, metric_id: str, nifi: NiFiClient):
    """
    Unprocess Metric
    """
    logger.info("Unprocessing metric with name %s" % (
        metric.metricname))
    logger.info(
        "Deleting '{0}'...".format(metric.metricname))
    # Renew access token for NiFi API
    nifi.login()
    nifi.delete_flow_from_metric(metric, metric_id)
