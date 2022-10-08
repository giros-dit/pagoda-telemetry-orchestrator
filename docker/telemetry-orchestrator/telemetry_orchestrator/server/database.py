import motor.motor_asyncio
import os
import logging
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGO_URL")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)

database_metrics = client.metrics

database_ue_location = client.ue_location

metric_collection = database_metrics.get_collection("metrics_collection")

ue_location_collection = database_ue_location.get_collection("ue_location_collection")


# Metric helper
def metric_helper(metric) -> dict:
    return {
        "id": str(metric["_id"]),
        "site": metric["site"],
        "metricname": metric["metricname"],
        "operation": metric["operation"],
        "labels": metric["labels"],
        "interval": metric["interval"],
        "description": metric["description"],
    }


# Retrieve all metrics present in the database
async def retrieve_metrics(site: str):
    metrics = []
    async for metric in metric_collection.find():
        if metric["site"] == site:
            metrics.append(metric_helper(metric))
    return metrics


# Add a new metric into to the database
async def add_metric(metric_data: dict) -> dict:
    # if metric_data.get('operation') is not None:
    #    metric_data['operation'] = _parseOperationSyntax
    metric = await metric_collection.insert_one(metric_data)
    new_metric = await metric_collection.find_one({"_id": metric.inserted_id})
    return metric_helper(new_metric)


# Retrieve a metric with a matching ID
async def retrieve_metric(site: str, id: str) -> dict:
    metric = await metric_collection.find_one({"_id": ObjectId(id)})
    if metric and metric["site"] == site:
        return metric_helper(metric)


# Update a metric with a matching ID
async def update_metric(site: str, id: str, data: dict):
    # Return false if an empty request body is sent.
    if len(data) < 1:
        return False
    metric = await metric_collection.find_one({"_id": ObjectId(id)})
    if metric and metric["site"] == site:
        updated_metric = await metric_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_metric:
            return True
        return False


# Delete a metric from the database
async def delete_metric(site: str, id: str):
    metric = await metric_collection.find_one({"_id": ObjectId(id)})
    if metric and metric["site"] == site:
        await metric_collection.delete_one({"_id": ObjectId(id)})
        return True

"""
def _parseOperationSyntax(operation: str) -> str:
    
    #Parse syntax of the delimiter of a Prometheus operation when any condition 
    #of a label has an empty value. (e.g., {image!=""} -> {image!=\"\"})
    
    new_operation = ""
    for index in range(len(operation)):
        character = operation[index]
        if character == '"' and operation[index+1] == '"':
            new_operation = new_operation + "\"\""
        else:
            if not (character == '"' and operation[index-1] == '"'):
                new_operation = new_operation + character
        
    logger.info("Metric operation '{0}'.".format(new_operation))
    return new_operation
"""


# UE location helper
def ue_location_helper(ue_location) -> dict:
    return {
        "id": str(ue_location["_id"]),
        "interval": ue_location["interval"],
        "description": ue_location["description"],
    }


# Retrieve UE locations info present in the database
async def retrieve_ue_locations():
    ue_locations = []
    async for ue_location in ue_location_collection.find():
        ue_locations.append(ue_location_helper(ue_location))
    return ue_locations


# Add a new UE location into to the database
async def add_ue_location(ue_location_data: dict) -> dict:
    ue_location = await ue_location_collection.insert_one(ue_location_data)
    new_ue_location = await ue_location_collection.find_one({"_id": ue_location.inserted_id})
    return ue_location_helper(new_ue_location)


# Retrieve UE location with a matching ID
async def retrieve_ue_location(id: str) -> dict:
    ue_location = await ue_location_collection.find_one({"_id": ObjectId(id)})
    if ue_location:
        return ue_location_helper(ue_location)


# Update a UE location interval with a matching ID
async def update_ue_location(id: str, data: dict):
    # Return false if an empty request body is sent.
    if len(data) < 1:
        return False
    ue_location = await ue_location_collection.find_one({"_id": ObjectId(id)})
    if ue_location:
        updated_ue_location = await ue_location_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_ue_location:
            return True
        return False


# Delete a UE location from the database
async def delete_ue_location(id: str):
    ue_location = await ue_location_collection.find_one({"_id": ObjectId(id)})
    if ue_location:
        await ue_location_collection.delete_one({"_id": ObjectId(id)})
        return True