import logging

from telemetry_orchestrator.server.models.metric import (
    MetricModel
)

from telemetry_orchestrator.server.models.ue_location import (
    UELocationModel
)

from telemetry_orchestrator.server.nificlient import NiFiClient

from telemetry_orchestrator.server.applications import nifi_application_configs

logger = logging.getLogger(__name__)


def process_metric(metric: MetricModel, metric_id: str, nifi: NiFiClient):
    """
    Process Metric
    """
    logger.info("Processing metric with name %s" % (
        metric.metricname))
    logger.info(
        "Instantiating new '{0}' NiFi Process Group...".format(
            metric.metricname+":"+metric_id))
    # Renew access token for NiFi API
    nifi.login()
    arguments = nifi_application_configs[
        "MetricSourceYANG"](metric, metric_id)
    nifi.instantiate_flow_from_metric(
        metric, metric_id, "MetricSourceYANG", arguments)


def reprocess_metric(metric: MetricModel, metric_id: str, nifi: NiFiClient):
    """
    Reprocess Metric
    """
    logger.info("Reprocessing metric with name %s" % (
        metric.metricname))
    logger.info(
        "Updating '{0}' NiFi Process Group...".format(
            metric.metricname+":"+metric_id))
    # Renew access token for NiFi API
    nifi.login()
    arguments = nifi_application_configs[
        "MetricSourceYANG"](metric, metric_id)
    nifi.update_flow_from_metric(metric, metric_id, arguments)


def unprocess_metric(metric: MetricModel, metric_id: str, nifi: NiFiClient):
    """
    Unprocess Metric
    """
    logger.info("Unprocessing metric with name %s" % (
        metric.metricname))
    logger.info(
        "Deleting '{0}' NiFi Process Group...".format(
            metric.metricname+":"+metric_id))
    # Renew access token for NiFi API
    nifi.login()
    nifi.delete_flow_from_metric(metric, metric_id)


def process_ue_location(ue_location: UELocationModel, ue_location_id: str, 
                        nifi: NiFiClient):
    """
    Process UE location
    """
    logger.info("Processing UE location")
    logger.info(
        "Instantiating new '{0}' NiFi Process Group...".format(
            ue_location_id))
    # Renew access token for NiFi API
    nifi.login()
    arguments = nifi_application_configs[
        "NDACSource"](ue_location, ue_location_id)
    nifi.instantiate_flow_from_ue_location(
        ue_location, ue_location_id, "NDACSource", arguments)


def reprocess_ue_location(ue_location: UELocationModel, ue_location_id: str, 
                          nifi: NiFiClient):
    """
    Reprocess UE location
    """
    logger.info("Reprocessing UE location")
    logger.info(
        "Updating '{0}' NiFi Process Group...".format(
            ue_location_id))
    # Renew access token for NiFi API
    nifi.login()
    arguments = nifi_application_configs[
        "NDACSource"](ue_location, ue_location_id)
    nifi.update_flow_from_ue_location(ue_location, ue_location_id, arguments)


def unprocess_ue_location(ue_location: UELocationModel, ue_location_id: str, 
                          nifi: NiFiClient):
    """
    Unprocess UE location
    """
    logger.info("Unprocessing UE location")
    logger.info(
        "Deleting '{0}' NiFi Process Group...".format(
            ue_location_id))
    # Renew access token for NiFi API
    nifi.login()
    nifi.delete_flow_from_ue_location(ue_location, ue_location_id)