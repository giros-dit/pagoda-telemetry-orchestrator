import logging
import os
import shutil
import time
from typing import Literal, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from process_manager.nificlient import NiFiClient

from process_manager import loader

logger = logging.getLogger(__name__)

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
    loader.upload_local_nifi_templates(
        nifi)


@app.post("/applications/")
async def onboard_application(application_type: Literal["NIFI"],
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

    return {"ID": application["application_id"]}