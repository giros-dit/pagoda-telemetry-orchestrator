import logging
import os
from fastapi import FastAPI
from telemetry_orchestrator.server.routes.metric import router as MetricRouter
from http import client

logger = logging.getLogger(__name__)

SITE_ID = os.getenv("SITE_ID")

app = FastAPI(
    title="Telemetry Orchestrator API",
    version="1.0.0")

app.include_router(MetricRouter, tags=["Metric"], prefix="/metric/"+SITE_ID)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Telemetry Orchestrator API!"}