from curses import beep
from xxlimited import new
from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
import logging
import os
import time
import requests
import subprocess


from telemetry_orchestrator.server.database import (
    add_metric,
    delete_metric,
    retrieve_metric,
    retrieve_metrics,
    update_metric,
)
from telemetry_orchestrator.server.models.metric import (
    SiteModel,
    MetricModel,
    UpdateMetricModel,
    ResponseModel,
    AddMetricResponseModel,
    GetMetricResponseModel,
    GetMetricsResponseModel,
    UpdateMetricResponseModel,
    DeleteMetricResponseModel
)

from telemetry_orchestrator.server.nificlient import NiFiClient

from telemetry_orchestrator.server.orchestration import (
    process_metric, 
    reprocess_metric, 
    unprocess_metric
)

router = APIRouter()

logger = logging.getLogger(__name__)


# NiFi
NIFI_URI = os.getenv("NIFI_URI", "https://nifi:8443/nifi-api")
NIFI_USERNAME = os.getenv("NIFI_USERNAME")
NIFI_PASSWORD = os.getenv("NIFI_PASSWORD")

# Prometheus
PROMETHEUS_URI = os.getenv("PROMETHEUS_URI")


# Init NiFi REST API Client
nifi = NiFiClient(username=NIFI_USERNAME,
                  password=NIFI_PASSWORD,
                  url=NIFI_URI)


'''
@router.on_event("startup")
async def startup_event():
    # Check NiFi REST API is up
    # Hack for startup
    while True:
        try:
            nifi.login()
            break
        except Exception:
            logger.warning("NiFi REST API not available. "
                           "Retrying after 10 seconds...")
            time.sleep(10)
    # Deploy DistributedMapCacheServer in root PG
    nifi.deploy_distributed_map_cache_server()
    # Deploy exporter-service PG in root PG
    nifi.deploy_exporter_service()
'''


def checkPrometheusEndpoint() -> bool:
    """
    Function to check if Prometheus server is reachable.
    """
    prometheus_reachable = False
    try:
        response = requests.get("{0}?query=prometheus_build_info".format(PROMETHEUS_URI))
        response.raise_for_status()
        if response.status_code == 200:
            logger.info(
                "Prometheus endpoint reachable."
            )
            prometheus_reachable = True
    except requests.exceptions.RequestException as err:
        logger.info(
            "The action failed. A request error exception occurred: '{0}'".format(err)
        )
        
    return prometheus_reachable


def checkPrometheusMetric(prometheus_query: str) -> bool:
    """
    Fuction to check if Prometheus metric exists.
    """
    prometheus_reachable = False
    try:
        response = requests.get("{0}?{1}".format(PROMETHEUS_URI, prometheus_query))
        response.raise_for_status()
        
        if response.status_code == 200 and len(response.json()['data']['result']) != 0:
            logger.info(
                "Prometheus metric '{0}' exists.".format(prometheus_query)
            )
            prometheus_reachable = True
    except requests.exceptions.RequestException as err:
        logger.info(
            "The action failed. A request error exception occurred: '{0}'".format(err)
        )
        
    return prometheus_reachable


def _getQueryLabels(expression: dict) -> str:
    """
    Print Prometheus labels to make them consumable
    by Prometheus REST API.
    """
    labels = []
    for label, value in expression.items():
        labels.append("{0}='{1}'".format(label, value))

    return ",".join(labels)


@router.post("/{site}", response_description="Metric added into the database", 
             response_model=AddMetricResponseModel)
async def add_metric_data(site: SiteModel, metric: MetricModel = Body(...)):
    
    metric = jsonable_encoder(metric)
    metric["site"] = site
    new_metric = await add_metric(metric)
    
    logger.info("New Metric '{0}'.".format(new_metric))
    metric_obj = MetricModel.parse_obj(new_metric)

    metric_name = ""
    if metric_obj.operation:
        metric_name = metric_obj.operation
    else:
        metric_name = metric_obj.metricname

    prometheus_request = ""
    if metric_obj.labels:
        labels = _getQueryLabels(metric_obj.labels)
        prometheus_request = (
            "query=" + metric_name +
            "{" + labels + "}")
    else:
        prometheus_request = ("query=" + metric_name)  

    detail_message = ""
    check_prometheus = checkPrometheusEndpoint()
    check_prometheus_metric = checkPrometheusMetric(prometheus_request)
    if new_metric and check_prometheus and check_prometheus_metric:
        process_metric(metric_obj, new_metric['id'], nifi)
        return ResponseModel(
            data=new_metric, code=200, message="Metric added successfully.")
    else: 
        if not check_prometheus:
            detail_message = "Prometheus server doesn't exist."
        else:
            if not check_prometheus_metric:
                detail_message = "Prometheus metric doesn't exist."
    raise HTTPException(
        status_code=404, detail="An error occurred. " + detail_message)

 
@router.get("/{site}", response_description="Metrics retrieved", 
            response_model=GetMetricsResponseModel)
async def get_metrics_data(site: SiteModel):
    metrics = await retrieve_metrics(site)
    if metrics:
        return ResponseModel(data=metrics, code=200, 
                             message="Metrics data retrieved successfully.")
    return ResponseModel(
        data=metrics, code=200, message="Empty list returned.")


@router.get("/{site}/{id}", response_description="Metric data retrieved", 
            response_model=GetMetricResponseModel)
async def get_metric_data(site: SiteModel, id: str):
    metric = await retrieve_metric(site, id)
    if metric:
        return ResponseModel(
            data=metric, message="Metric data retrieved successfully.")
    raise HTTPException(
        status_code=404, detail="An error occurred. " +
        "Metric with ID {0} doesn't exist in site {1}.".format(id, str(site.value)))


@router.put("/{site}/{id}", response_description="Metric data updated", 
            response_model=UpdateMetricResponseModel)
async def update_metric_data(site: SiteModel, id: str, req: UpdateMetricModel = Body(...)):
    metric = await retrieve_metric(site, id)
    if metric:
        req = {k: v for k, v in req.dict().items() if v is not None}
        updated_metric = await update_metric(site, id, req)
        if updated_metric:
            new_metric = await retrieve_metric(site, id)
            logger.info("Updated Metric '{0}'.".format(new_metric))
            new_metric_obj = MetricModel.parse_obj(new_metric)
            reprocess_metric(new_metric_obj, new_metric['id'], nifi)
            return ResponseModel(
                data="Metric with ID {0} updated.".format(id),
                code=200,
                message="Metric data updated successfully."
            )
    raise HTTPException(
        status_code=404, 
        detail="An error occurred. " + 
        "Metric with ID {0} doesn't exist in site {1}.".format(id, str(site.value))
    )


@router.delete(
    "/{site}/{id}", response_description="Metric deleted from the database", 
    response_model=DeleteMetricResponseModel)
async def delete_metric_data(site: SiteModel, id: str):
    metric = await retrieve_metric(site, id)
    if metric:
        deleted_metric = await delete_metric(site, id)
        if deleted_metric:
            metric_obj = MetricModel.parse_obj(metric)
            unprocess_metric(metric_obj, metric['id'], nifi)
            return ResponseModel(
                data="Metric with ID {0} removed.".format(id), 
                code=200,
                message="Metric deleted successfully."
            )
    raise HTTPException(
        status_code=404, 
        detail="An error occurred. " + 
        "Metric with ID {0} doesn't exist in site {1}.".format(id, str(site.value))
    )