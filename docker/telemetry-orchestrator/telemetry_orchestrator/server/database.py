import motor.motor_asyncio
from bson.objectid import ObjectId


MONGO_DETAILS = "mongodb://mongo-db:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.metrics

metric_collection = database.get_collection("metrics_collection")


# helpers
def metric_helper(metric) -> dict:
    return {
        "id": str(metric["_id"]),
        "metricname": metric["metricname"],
        "labels": metric["labels"],
        "interval": metric["interval"],
        "description": metric["description"],
    }


# Retrieve all metrics present in the database
async def retrieve_metrics():
    metrics = []
    async for metric in metric_collection.find():
        metrics.append(metric_helper(metric))
    return metrics


# Add a new metric into to the database
async def add_metric(metric_data: dict) -> dict:
    metric = await metric_collection.insert_one(metric_data)
    new_metric = await metric_collection.find_one({"_id": metric.inserted_id})
    return metric_helper(new_metric)


# Retrieve a metric with a matching ID
async def retrieve_metric(id: str) -> dict:
    metric = await metric_collection.find_one({"_id": ObjectId(id)})
    if metric:
        return metric_helper(metric)


# Update a metric with a matching ID
async def update_metric(id: str, data: dict):
    # Return false if an empty request body is sent.
    if len(data) < 1:
        return False
    metric = await metric_collection.find_one({"_id": ObjectId(id)})
    if metric:
        updated_metric = await metric_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_metric:
            return True
        return False


# Delete a metric from the database
async def delete_metric(id: str):
    metric = await metric_collection.find_one({"_id": ObjectId(id)})
    if metric:
        await metric_collection.delete_one({"_id": ObjectId(id)})
        return True