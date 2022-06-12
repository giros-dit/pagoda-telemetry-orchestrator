import logging
import os
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from app_manager.nificlient import NiFiClient

from app_manager import loader

logger = logging.getLogger(__name__)


# Application Manager
APP_MANAGER_URI = os.getenv("APP_MANAGER_URI", "http://app-manager:8080")

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
    title="Application Manager API",
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
        nifi, APP_MANAGER_URI)
