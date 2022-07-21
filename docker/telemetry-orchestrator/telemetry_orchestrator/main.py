import logging
import os
import time
from fastapi import FastAPI
from telemetry_orchestrator.server.routes.metric import router as MetricRouter
from telemetry_orchestrator.server.routes.ue_location import router as UELocationRouter
from telemetry_orchestrator.server.nificlient import NiFiClient
from http import client

logger = logging.getLogger(__name__)

SITE_ID = os.getenv("SITE_ID")

# NiFi
NIFI_URI = os.getenv("NIFI_URI", "https://nifi:8443/nifi-api")
NIFI_USERNAME = os.getenv("NIFI_USERNAME")
NIFI_PASSWORD = os.getenv("NIFI_PASSWORD")

# Init NiFi REST API Client
nifi = NiFiClient(username=NIFI_USERNAME,
                  password=NIFI_PASSWORD,
                  url=NIFI_URI)

app = FastAPI(
    title="Telemetry Orchestrator API",
    version="1.0.0")


@app.on_event("startup")
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
    # nifi.deploy_distributed_map_cache_server()
    # Deploy exporter-service PG in root PG
    # nifi.deploy_exporter_service()


app.include_router(MetricRouter, tags=["Prometheus Metrics"], prefix="/metric/"
                   + str(SITE_ID))

app.include_router(UELocationRouter, tags=["UE Location"], prefix="/ue-location")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Telemetry Orchestrator API!"}
