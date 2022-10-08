from curses import beep
from xxlimited import new
from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
import logging
import os
import time
import requests
import subprocess
import yaml


from process_manager.database import (
    add_alert,
    delete_alert,
    retrieve_alerts,
    retrieve_alert
)
from process_manager.models.alerts import (
    AlertModel,
    ResponseModel,
    AddAlertResponseModel,
    GetAlertResponseModel,
    GetAlertsResponseModel,
    DeleteAlertResponseModel
)

from process_manager.nificlient import NiFiClient

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


@router.post("", response_description="Alert added into the database", 
             response_model=AddAlertResponseModel)
async def add_alert_data(alert: AlertModel = Body(...)):  
    alert = jsonable_encoder(alert)
    new_alert = await add_alert(alert)

    logger.info("New Alert '{0}'.".format(new_alert))
    alert_obj = AlertModel.parse_obj(new_alert)

    detail_message = ""
    if new_alert:
        # Store Proemetheus alert rule in Prometheus repository
        prom_folder = "/opt/process-manager/process_manager/prometheus-rules/single/"
        prom_filename = os.path.join(prom_folder, "%s.yml" % alert_obj.filename)  
        os.makedirs(prom_folder, exist_ok=True)
        # Store Prometheus alert rule in local catalog
        catalog_folder = "/opt/process-manager/process_manager/catalog/alert/rules/single/"
        catalog_filename = os.path.join(catalog_folder, "%s.yml" % alert_obj.filename)  
        os.makedirs(catalog_folder, exist_ok=True)
        prom_rule = {}
        groups = {}
        group = {}
        rules = {}
        alert = {}
        annotations = {}
        annotations['summary'] = alert_obj.summary
        annotations['description'] = alert_obj.description
        labels = {}
        labels['severity'] = alert_obj.severity
        alert['expr'] = alert_obj.expr
        alert['for'] = alert_obj.duration
        alert['labels'] = labels
        alert['annotations'] = annotations
        alert['alert'] = alert_obj.alertname
        rules = [alert]
        group['rules'] = rules
        group['name'] = alert_obj.rulename
        groups = [group]
        prom_rule['groups'] = groups

        with open(prom_filename, 'w') as file:
            yaml.dump(prom_rule, file)

        with open(catalog_filename, 'w') as file:    
            yaml.dump(prom_rule, file)

        return ResponseModel(
            data=new_alert, code=200, message="Alert added successfully.")
    raise HTTPException(
        status_code=404, detail="An error occurred. " + detail_message)

 
@router.get("", response_description="Alerts retrieved", 
            response_model=GetAlertsResponseModel)
async def get_alerts_data():
    alerts = await retrieve_alerts()
    if alerts:
        return ResponseModel(data=alerts, code=200, 
                             message="Alerts data retrieved successfully.")
    return ResponseModel(
        data=alerts, code=200, message="Empty list returned.")


@router.get("/{id}", response_description="Alert data retrieved", 
            response_model=GetAlertResponseModel)
async def get_alert_data(id: str):
    alert = await retrieve_alert(id)
    if alert:
        return ResponseModel(
            data=alert, message="Alert data retrieved successfully.")
    raise HTTPException(
        status_code=404, detail="An error occurred. " +
        "Alert with ID {0} doesn't exist.".format(id))


@router.delete(
    "/{id}", response_description="Alert deleted from the database", 
    response_model=DeleteAlertResponseModel)
async def delete_alert_data(id: str):
    alert = await retrieve_alert(id)
    if alert:
        deleted_alert = await delete_alert(id)
        if deleted_alert:
            alert_obj = AlertModel.parse_obj(alert)
            prom_filename = ('/opt/process-manager/process_manager/prometheus-rules/single/' + alert_obj.filename + '.yml')
            catalog_filename = "/opt/process-manager/process_manager/catalog/alert/rules/single/%s.yml" % alert_obj.filename
            os.remove(prom_filename)
            os.remove(catalog_filename)
            return ResponseModel(
                data="Alert with ID {0} removed.".format(id), 
                code=200,
                message="Alert deleted successfully."
            )
    raise HTTPException(
        status_code=404, 
        detail="An error occurred. " + 
        "Alert with ID {0} doesn't exist.".format(id)
    )