from curses import beep
from xxlimited import new
from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
import logging
import os
import time


from telemetry_orchestrator.server.database import (
    add_ue_location,
    delete_ue_location,
    retrieve_ue_location,
    retrieve_ue_locations,
    update_ue_location
)

from telemetry_orchestrator.server.models.ue_location import (
    UELocationModel,
    UpdateUELocationModel,
    ResponseModel,
    AddUELocationResponseModel,
    GetUELocationsResponseModel,
    UpdateUELocationResponseModel,
    DeleteUELocationResponseModel
)

from telemetry_orchestrator.server.nificlient import NiFiClient

from telemetry_orchestrator.server.orchestration import (
    process_ue_location, 
    reprocess_ue_location, 
    unprocess_ue_location
)

router = APIRouter()

logger = logging.getLogger(__name__)

# NiFi
NIFI_URI = os.getenv("NIFI_URI")
NIFI_USERNAME = os.getenv("NIFI_USERNAME")
NIFI_PASSWORD = os.getenv("NIFI_PASSWORD")

# Init NiFi REST API Client
nifi = NiFiClient(username=NIFI_USERNAME,
                  password=NIFI_PASSWORD,
                  url=NIFI_URI)


@router.post("/", response_description="UE location added into the database", 
             response_model=AddUELocationResponseModel)
async def activate_ue_location(ue_location: UELocationModel = Body(...)):
    ue_location = jsonable_encoder(ue_location)
    new_ue_location = await add_ue_location(ue_location)
    logger.info("New UE location '{0}'.".format(new_ue_location))
    ue_location_obj = UELocationModel.parse_obj(new_ue_location)
    process_ue_location(ue_location_obj, new_ue_location['id'], nifi)
    return ResponseModel(
        data=new_ue_location, code=200, message="UE location activated successfully.")


@router.get("/", response_description="UE location retrieved", 
            response_model=GetUELocationsResponseModel)
async def get_ue_location_interval():
    ue_locations = await retrieve_ue_locations()
    if ue_locations:
        return ResponseModel(data=ue_locations, code=200, 
                             message="UE location interval retrieved successfully.")
    return ResponseModel(
        data=ue_locations, code=200, message="Empty list returned.")


@router.put("/{id}", response_description="UE location interval updated", 
            response_model=UpdateUELocationResponseModel)
async def update_ue_location_interval(id: str, req: UpdateUELocationModel = Body(...)):
    ue_location = await retrieve_ue_location(id)
    if ue_location:
        req = {k: v for k, v in req.dict().items() if v is not None}
        updated_ue_location = await update_ue_location(id, req)
        if updated_ue_location:
            new_ue_location = await retrieve_ue_location(id)
            logger.info("Updated UE location '{0}'.".format(new_ue_location))
            new_ue_location_obj = UELocationModel.parse_obj(new_ue_location)
            reprocess_ue_location(new_ue_location_obj, new_ue_location['id'], nifi)
            return ResponseModel(
                data="UE location process with ID {} updated.".format(id),
                code=200,
                message="UE location interval updated successfully."
            )
    raise HTTPException(
        status_code=404, 
        detail="An error occurred. " + 
        "UE location process with ID {0} doesn't exist.".format(id)
    )


@router.delete(
    "/{id}", response_description="UE location deleted from the database", 
    response_model=DeleteUELocationResponseModel)
async def desactivate_ue_location(id: str):
    ue_location = await retrieve_ue_location(id)
    if ue_location:
        deleted_ue_location  = await delete_ue_location(id)
        if deleted_ue_location:
            ue_location_obj = UELocationModel.parse_obj(ue_location)
            unprocess_ue_location(ue_location_obj, ue_location['id'], nifi)
            return ResponseModel(
                data="UE location process with ID {} removed.".format(id), 
                code=200,
                message="UE location desactivated successfully."
            )
    raise HTTPException(
        status_code=404, 
        detail="An error occurred. " + 
        "UE location process with ID {0} doesn't exist.".format(id)
    )