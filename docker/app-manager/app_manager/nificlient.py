import logging
import time
from random import randrange
from typing import List

import nipyapi
from nipyapi import parameters as nifi_params
from nipyapi.nifi import ParameterContextEntity, ParameterEntity
from nipyapi.nifi.models.controller_service_entity import \
    ControllerServiceEntity
from nipyapi.nifi.models.documented_type_dto import DocumentedTypeDTO
from nipyapi.nifi.models.process_group_entity import ProcessGroupEntity
from nipyapi.nifi.models.process_group_flow_entity import \
    ProcessGroupFlowEntity
from nipyapi.nifi.models.template_entity import TemplateEntity

logger = logging.getLogger(__name__)

EXPORTER_SERVICE_PG_NAME = "exporter-service"


class NiFiClient(object):
    """
    Class encapsulating the main operations with Apache NiFi.
    """

    def __init__(self,
                 username: str,
                 password: str,
                 url: str = "https://nifi:8443/nifi-api",):

        self.username = username
        self.password = password
        self.url = url

        # Init NiFi REST API Client
        nipyapi.config.nifi_config.host = url
        # Disable SSL verification
        nipyapi.config.nifi_config.verify_ssl = False

    def login(self):
        """
        Log into NiFi to generate temporary token
        """
        logger.info("Waiting for NiFi to be ready for login")
        nipyapi.utils.wait_to_complete(
            test_function=nipyapi.security.service_login,
            service='nifi',
            username=self.username,
            password=self.password,
            bool_response=True,
            nipyapi_delay=10,  # 10 sec
            nipyapi_max_wait=120  # 120 sec
        )
        nifi_user = nipyapi.security.get_service_access_status(service='nifi')
        logger.info(
            'nipyapi_secured_nifi CurrentUser: '
            + nifi_user.access_status.identity
        )

    def upload_template(self, template_path: str) -> TemplateEntity:
        """
        Uploads template to root process group
        """
        # Get root PG
        root_pg = nipyapi.canvas.get_process_group("root")
        template = nipyapi.templates.upload_template(
            root_pg.id, template_path)
        return template
