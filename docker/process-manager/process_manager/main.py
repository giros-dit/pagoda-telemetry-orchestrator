import logging
import os
import shutil
import time
import yaml

from typing import Literal, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from process_manager.alert import router as AlertRouter


from process_manager.nificlient import NiFiClient

from process_manager import loader

from process_manager.database import (
    add_alert
)

from process_manager.models.alerts import (
    AlertModel
)

logger = logging.getLogger(__name__)

#with open("/opt/process-manager/process_manager/prometheus-rules/server-rules1.yml") as file:
#    yml_obj = yaml.load(file, Loader=yaml.FullLoader)
#    print(yml_obj)

#dict_file = [{'sports' : ['soccer', 'football', 'basketball', 'cricket', 'hockey', 'table tennis']},
#{'countries' : ['Pakistan', 'USA', 'India', 'China', 'Germany', 'France', 'Spain']}]

#with open("/opt/process-manager/process_manager/prometheus-rules/example.yml", 'w') as file:
#    yaml.dump(dict_file, file)

# Process Manager
# PROCESS_MANAGER_URI = os.getenv("PROCESS_MANAGER_URI", "http://process-manager:8080")

# NiFi
NIFI_URI = os.getenv("NIFI_URI", "https://nifi:8443/nifi-api")
NIFI_USERNAME = os.getenv("NIFI_USERNAME")
NIFI_PASSWORD = os.getenv("NIFI_PASSWORD")

# Init NiFi REST API Client
nifi = NiFiClient(username=NIFI_USERNAME,
                  password=NIFI_PASSWORD,
                  url=NIFI_URI)

# Init FastAPI server
app = FastAPI(
    title="Process Manager API",
    version="1.0.0")

# Mount static catalog
script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, "catalog")
app.mount("/catalog", StaticFiles(directory=st_abs_file_path), name="catalog")


@app.on_event("startup")
async def startup_event():
    # Upload Prometheus alert admin rules
    loader.upload_local_alert_rules()
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
    # Upload NiFi admin templates
    loader.upload_local_nifi_templates(nifi)


@app.post("/applications", tags=["Default Processes Management"])
async def onboard_application(application_type: Literal["NIFI", "ALERT"],
                              name: str,
                              description: Optional[str] = None,
                              file: UploadFile = File(...)):
    contents = await file.read()
    application = None
    if application_type == "NIFI":
        # Write template to temporary file
        temp_folder = "/tmp/nifi/templates/"
        temp_path = os.path.join(temp_folder, "%s.xml" % name)
        os.makedirs(temp_folder, exist_ok=True)
        f = open(temp_path, "wb")
        f.write(contents)
        f.close()
        try:
            # Upload application to NiFi
            # Nipyapi runs check of file format for us
            # Moreover, the only way to find out the identifier
            # of the template, i.e. name, is by uploading it
            application = loader.upload_nifi_template(
                nifi, name, temp_path, description)
        except TypeError as e:
            logger.error(str(e))
            os.remove(temp_path)
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except ValueError as e:
            logger.error(str(e))
            os.remove(temp_path)
            raise HTTPException(
                status_code=409,
                detail=str(e)
            )
        # Store NiFI application in local catalog
        f_path = "/opt/process-manager/process_manager/catalog/nifi/templates/%s.xml" % application["name"]
        # f_path = "/opt/process-manager/process_manager/catalog/nifi/templates/%s.xml" % application["application_id"]

        shutil.move(temp_path, f_path)
    
    else:
        # Write template to temporary file
        temp_folder = "/tmp/prometheus/alerts/"
        temp_path = os.path.join(temp_folder, "%s.yml" % name)
        os.makedirs(temp_folder, exist_ok=True)
        f = open(temp_path, "wb")
        f.write(contents)
        f.close()
        try:
            # Upload Prometheus alert rule to Prometheus
            # Update name of alert rule file and copy to Prometheus alert repository
            foldername = '/opt/process-manager/process_manager/prometheus-rules/single'
            fullname = os.path.join(foldername, "%s.yml" % name)  
     
            with open(temp_path) as file:
                try:
                    original_rule_dict = yaml.load(file, Loader=yaml.FullLoader)
                    database_rule_dict = dict()
                    database_rule_dict['filename'] = name
                    database_rule_dict['rulename'] = original_rule_dict['groups'][0]['name']
                    database_rule_dict['alertname'] = original_rule_dict['groups'][0]['rules'][0]['alert']
                    database_rule_dict['expr'] = original_rule_dict['groups'][0]['rules'][0]['expr']
                    database_rule_dict['duration'] = original_rule_dict['groups'][0]['rules'][0]['for']
                    database_rule_dict['severity'] = original_rule_dict['groups'][0]['rules'][0]['labels']['severity']
                    database_rule_dict['summary'] = original_rule_dict['groups'][0]['rules'][0]['annotations']['summary']
                    database_rule_dict['description'] = original_rule_dict['groups'][0]['rules'][0]['annotations']['description']
                except KeyError as e:
                    logger.error(str(e))
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=400,
                        detail=str(e)
                    )
            new_alert = await add_alert(database_rule_dict)
            logger.info("New Alert '{0}'.".format(new_alert))
            alert_obj = AlertModel.parse_obj(new_alert)
            if new_alert:
                # Upload Prometheus alert rule to Prometheus
                shutil.copyfile(temp_path, fullname)
                # Store Prometheus alert rule in local catalog
                f_path = "/opt/process-manager/process_manager/catalog/alert/rules/single/%s.yml" % name
                application = dict()
                application["application_id"] = alert_obj.filename
                application["name"] = alert_obj.rulename
                application["description"] = alert_obj.description
                logger.info("Application information: {0}".format(application))
                shutil.move(temp_path, f_path)
        
        except TypeError as e:
            logger.error(str(e))
            os.remove(temp_path)
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except ValueError as e:
            logger.error(str(e))
            os.remove(temp_path)
            raise HTTPException(
                status_code=409,
                detail=str(e)
            )

    return {"ID": application["application_id"]}

app.include_router(AlertRouter, tags=["Prometheus Alerts"], prefix="/alerts")                   

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Process Manager API!"}