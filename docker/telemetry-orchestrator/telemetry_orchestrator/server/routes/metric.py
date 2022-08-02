from curses import beep
from xxlimited import new
from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
import logging
import os
import time


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


@router.post("/{site}", response_description="Metric added into the database", 
             response_model=AddMetricResponseModel)
async def add_metric_data(site: SiteModel, metric: MetricModel = Body(...)):
    metric = jsonable_encoder(metric)
    metric["site"] = site
    new_metric = await add_metric(metric)
    logger.info("New Metric '{0}'.".format(new_metric))
    metric_obj = MetricModel.parse_obj(new_metric)
    process_metric(metric_obj, new_metric['id'], nifi)
    return ResponseModel(
        data=new_metric, code=200, message="Metric added successfully.")


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