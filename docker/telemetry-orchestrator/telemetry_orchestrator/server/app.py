from http import client
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)
from telemetry_orchestrator.server.routes.metric import router as MetricRouter

app = FastAPI(
    title="Telemetry Orchestrator API",
    version="1.0.0")

app.include_router(MetricRouter, tags=["Metric"], prefix="/metric")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this Telemetry Orchestrator app!"}