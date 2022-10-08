import motor.motor_asyncio
import os
import logging
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGO_URL")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)

database_alerts = client.alerts

alert_collection = database_alerts.get_collection("alerts_collection")

# Alert helper
def alert_helper(alert) -> dict:
    return {
        "id": str(alert["_id"]),
        "rulename": alert["rulename"],
        "alertname": alert["alertname"],
        "expr": alert["expr"],
        "duration": alert["duration"],
        "severity": alert["severity"],
        "summary": alert["summary"],
        "description": alert["description"] 
    }

# Retrieve alerts info present in the database
async def retrieve_alerts():
    alerts = []
    async for alert in alert_collection.find():
        alerts.append(alert_helper(alert))
    return alerts

# Add a new alert into to the database
async def add_alert(alert_data: dict) -> dict:
    alert = await alert_collection.insert_one(alert_data)
    new_alert = await alert_collection.find_one({"_id": alert.inserted_id})
    return alert_helper(new_alert)

# Retrieve alert with a matching ID
async def retrieve_alert(id: str) -> dict:
    alert = await alert_collection.find_one({"_id": ObjectId(id)})
    if alert:
        return alert_helper(alert)

# Delete alert from the database
async def delete_alert(id: str):
    alert = await alert_collection.find_one({"_id": ObjectId(id)})
    if alert:
        await alert_collection.delete_one({"_id": ObjectId(id)})
        return True

# UE location helper
def ue_location_helper(ue_location) -> dict:
    return {
        "id": str(ue_location["_id"]),
        "interval": ue_location["interval"],
        "description": ue_location["description"],
    }