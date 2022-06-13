from curses import beep
from xxlimited import new
from fastapi import APIRouter, Body
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
    ErrorResponseModel,
    ResponseModel,
    MetricSchema,
    UpdateMetricModel,
)

from telemetry_orchestrator.server.nificlient import NiFiClient

from telemetry_orchestrator.server.orchestration import process_metric, reprocess_metric, unprocess_metric

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
    #nifi.deploy_distributed_map_cache_server()
    # Deploy exporter-service PG in root PG
    #nifi.deploy_exporter_service()
    # Check Flink REST API is up
    #flink.check_flink_status()


@router.post("/", response_description="Metric data added into the database")
async def add_metric_data(metric: MetricSchema = Body(...)):
    metric = jsonable_encoder(metric)
    new_metric = await add_metric(metric)
    logger.info("New Metric '{0}'.".format(new_metric))
    metric_obj = MetricSchema.parse_obj(new_metric)
    process_metric(metric_obj, new_metric['id'], nifi)
    return ResponseModel(new_metric, "Metric added successfully.")


@router.get("/", response_description="Metrics retrieved")
async def get_metrics():
    metrics = await retrieve_metrics()
    if metrics:
        return ResponseModel(metrics, "Metrics data retrieved successfully")
    return ResponseModel(metrics, "Empty list returned")


@router.get("/{id}", response_description="Metric data retrieved")
async def get_metric_data(id):
    metric = await retrieve_metric(id)
    if metric:
        return ResponseModel(metric, "Metric data retrieved successfully")
    return ErrorResponseModel(
            "An error occurred.", 404, "Metric doesn't exist.")


@router.put("/{id}")
async def update_metric_data(id: str, req: UpdateMetricModel = Body(...)):
    metric = await retrieve_metric(id)
    if metric:
        req = {k: v for k, v in req.dict().items() if v is not None}
        updated_metric = await update_metric(id, req)
        if updated_metric:
            logger.info("Updated Metric '{0}'.".format(updated_metric))
            new_metric = await retrieve_metric(id)
            logger.info("Updated Metric '{0}'.".format(new_metric))
            metric_obj = MetricSchema.parse_obj(metric)
            new_metric_obj = MetricSchema.parse_obj(new_metric)
            # reprocess_metric(metric_obj, new_metric_obj, nifi)
            reprocess_metric(new_metric_obj, new_metric['id'], nifi)
            return ResponseModel(
                "Metric with ID: {} name update is successful".format(id),
                "Metric name updated successfully",
            )
        return ErrorResponseModel(
            "An error occurred",
            404,
            "There was an error updating the metric data.",
        )
    return ErrorResponseModel(
            "An error occurred.", 404, "Metric with id {0} doesn't exist".format(id))

@router.delete(
    "/{id}", response_description="Metric data deleted from the database")
async def delete_metric_data(id: str):
    metric = await retrieve_metric(id)
    if metric:
        deleted_metric = await delete_metric(id)
        if deleted_metric:
            metric_obj = MetricSchema.parse_obj(metric)
            unprocess_metric(metric_obj, metric['id'], nifi)
            return ResponseModel(
                "Metric with ID: {} removed".format(id), 
                "Metric deleted successfully"
            )
    return ErrorResponseModel(
            "An error occurred.", 404, "Metric with id {0} doesn't exist".format(id))