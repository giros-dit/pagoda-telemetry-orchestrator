import logging
import os
from typing import Optional
from xml.etree import ElementTree as et

from app_manager.nificlient import NiFiClient

logger = logging.getLogger(__name__)

# Config catalog paths
script_dir = os.path.dirname(__file__)
TEMPLATES_PATH = os.path.join(script_dir, "catalog", "nifi", "templates/")


def upload_local_nifi_templates(
        nifi: NiFiClient,
        app_manager_url: str):
    """
    Upload NiFi templates stored locally in the service.
    """
    # Upload templates
    for file in os.listdir(TEMPLATES_PATH):
        logger.info("Uploading '%s' admin template to NiFi..." % file)
        try:
            template = nifi.upload_template(
                        TEMPLATES_PATH + file)
        except Exception as e:
            logger.info(str(e))
            continue
        logger.info("Template with ID '{0}' uploaded.".format(template.id))
        logger.info("Template information '{0}': ".format(template))
