import logging
import time
import hashlib
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
from telemetry_orchestrator.server.models.metric import (
    ErrorResponseModel,
    ResponseModel,
    MetricSchema,
    UpdateMetricModel,
)

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

    def prepare_parameters_for_context(
            self, params: dict) -> List[ParameterEntity]:
        """
        Generates a list of ParameterEntity from a given dictionary.
        Useful method to produce a list which can be used to feed
        the create_parameter_context mehtod.
        """
        param_entities = []
        for key, value in params.items():
            param = nifi_params.prepare_parameter(key, value)
            param_entities.append(param)
        return param_entities

    def set_parameter_context(
            self, pg: ProcessGroupEntity,
            params: dict) -> ParameterContextEntity:
        """
        Creates a parameter context from a given dictionary.
        The context is assigned to the specified process group (by ID).
        """
        param_entities = self.prepare_parameters_for_context(params)
        context = nifi_params.create_parameter_context(
            pg.id, parameters=param_entities)
        nifi_params.assign_context_to_process_group(pg, context.id)
        return context

    def create_controller_service(
            self, pg: ProcessGroupEntity,
            dto: DocumentedTypeDTO,
            name: str = None) -> ControllerServiceEntity:
        """
        Creates Controller Service from a given DocumentedTypeDTO.
        Optionally, the controller service can be created under a
        specified a name.
        """
        return nipyapi.canvas.nipyapi.canvas.create_controller(
            pg, dto, name)

    def delete_flow_from_metric(self, metric: MetricSchema):
        """
        Delete MetricSchema flow.
        """
        # Stop process group
        metric_pg = self.stop_flow_from_metric(metric)
        # Disable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(
            metric_pg.id, False)
        if controllers:
            for controller in controllers:
                if controller.status.run_status == 'ENABLED':
                    logger.debug("Disabling controller %s ..."
                                 % controller.component.name)
                    nipyapi.canvas.schedule_controller(
                        controller, False, True)
        # Delete Metric PG
        nipyapi.canvas.delete_process_group(metric_pg, True)
        pg_name = self.processgroup_name(metric)
        logger.debug("'{0}' flow deleted in NiFi.".format(pg_name))

    def deploy_distributed_map_cache_server(
            self, pg: ProcessGroupEntity = None,
            name: str = None) -> ControllerServiceEntity:
        """
        Creates Distributed Map Cache Server service in NiFi.
        """
        cs_name = "DistributedMapCacheServer"
        if pg:
            target_pg = pg
        else:
            target_pg = self.get_root_pg()

        if self.get_controller_service(target_pg, cs_name):
            logger.debug("{0} already deployed in {1}".format(
                cs_name, target_pg.id))
            return None
        else:
            cs_type = self.get_controller_service_type(cs_name)
            cs = self.create_controller_service(target_pg, cs_type, name)
            return self.enable_controller_service(cs)

    def deploy_exporter_service(self) -> ProcessGroupEntity:
        """
        Deploys export-service NiFi template
        """
        # Get root PG
        root_pg = nipyapi.canvas.get_process_group("root")
        # Check if already deployed, return if found
        exporter_service_pg = nipyapi.canvas.get_process_group(
            EXPORTER_SERVICE_PG_NAME)
        if exporter_service_pg:
            return exporter_service_pg
        # Deploy template
        # Avoid race conditions due to app-manager microservice
        template = None
        while(not template):
            logger.info(
                "Waiting for exporter-service template to become available")
            template = nipyapi.templates.get_template(EXPORTER_SERVICE_PG_NAME)
            time.sleep(10)

        _ = nipyapi.templates.deploy_template(
            root_pg.id,
            template.id,
            -250, 200)
        exporter_service_pg = nipyapi.canvas.get_process_group(
            EXPORTER_SERVICE_PG_NAME)
        # Enable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(
            exporter_service_pg.id, False)
        if controllers:
            # Enable controller services
            # Start with the registry controller
            for controller in controllers:
                logger.debug(
                    "Enabling controller %s ..."
                    % controller.component.name)
                if controller.status.run_status != 'ENABLED':
                    nipyapi.canvas.schedule_controller(controller, True)
        # Schedule PG
        nipyapi.canvas.schedule_process_group(exporter_service_pg.id, True)
        logger.info(
            "exporter-service PG with ID '{0}' deployed in NiFi.".format(
                exporter_service_pg.id))
        return exporter_service_pg

    def delete_exporter_service(self):
        """
        Delete special exporter-service process group
        """
        # Stop process group
        exporter_pg = nipyapi.canvas.get_process_group(
            EXPORTER_SERVICE_PG_NAME)
        # Disable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(
            exporter_pg.id, False)
        if controllers:
            for controller in controllers:
                if controller.status.run_status == 'ENABLED':
                    logger.debug("Disabling controller %s ..."
                                 % controller.component.name)
                    nipyapi.canvas.schedule_controller(
                        controller, False, True)
        # Delete Metric PG
        nipyapi.canvas.delete_process_group(exporter_pg, True)
        logger.info("'{0}' flow deleted in NiFi.".format(exporter_pg.id))

    def deploy_flow_from_metric(self, metric: MetricSchema, application_name: str,
                              args: dict) -> ProcessGroupEntity:
        """
        Deploys a NiFi template
        from a passed MetricSchema model.
        """
        # Get root PG
        root_pg = nipyapi.canvas.get_process_group("root")
        # Place the PG in a random location in canvas
        location_x = randrange(0, 4000)
        location_y = randrange(0, 4000)
        location = (location_x, location_y)
        pg_name = self.processgroup_name(metric)
        metric_pg = nipyapi.canvas.create_process_group(
            root_pg, pg_name, location
        )
        logger.debug("Deploy with arguments %s" % args)
        # Set Parameter Context for Metric PG
        self.set_parameter_context(metric_pg, args)

        # Deploy Metric template
        metric_template = nipyapi.templates.get_template_by_name(application_name)
        metric_pg_flow = nipyapi.templates.deploy_template(
            metric_pg.id,
            metric_template.id,
            -250, 200)
        # Enable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(metric_pg.id, False)
        if controllers:
            # Enable controller services
            # Start with the registry controller
            for controller in controllers:
                logger.debug(
                    "Enabling controller %s ..."
                    % controller.component.name)
                if controller.status.run_status != 'ENABLED':
                    nipyapi.canvas.schedule_controller(controller, True)
        # Hack to support scheduling for a given processor
        if "interval" in args:
            self.set_polling_interval(metric_pg_flow, args["interval"])

        logger.debug("'{0}' flow deployed in NiFi.".format(pg_name))
        return metric_pg

    def instantiate_flow_from_metric(self, metric: MetricSchema, application_name: str,
                                   args: dict) -> ProcessGroupEntity:
        """
        Deploys and starts NiFi template given a MetricSchema.
        """
        metric_pg = self.deploy_flow_from_metric(metric, application_name, args)
        # Schedule PG
        nipyapi.canvas.schedule_process_group(metric_pg.id, True)
        pg_name = self.processgroup_name(metric)
        logger.debug(
            "'{0}' flow scheduled in NiFi.".format(pg_name))
        return metric_pg   

    def start_flow_from_metric(self, metric: MetricSchema) -> ProcessGroupEntity:
        """
        Starts NiFi flow given a MetricSchema.
        """
        # Schedule PG
        pg_name = self.processgroup_name(metric)
        metric_pg = nipyapi.canvas.get_process_group(pg_name)
        nipyapi.canvas.schedule_process_group(metric_pg.id, True)
        logger.debug(
            "'{0}' flow scheduled in NiFi.".format(pg_name))
        return metric_pg

    def stop_flow_from_metric(self, metric: MetricSchema) -> ProcessGroupEntity:
        """
        Stop NiFi flow (Process Group) from MetricSchema.
        """
        pg_name = self.processgroup_name(metric)
        metric_pg = nipyapi.canvas.get_process_group(pg_name)
        nipyapi.canvas.schedule_process_group(metric_pg.id, False)
        logger.debug(
            "'{0}' flow unscheduled in NiFi.".format(pg_name))
        return metric_pg

    def disable_controller_service(
            self,
            controller: ControllerServiceEntity) -> ControllerServiceEntity:
        """
        Disables controller service.
        """
        return nipyapi.canvas.schedule_controller(controller, False)

    def enable_controller_service(
            self,
            controller: ControllerServiceEntity) -> ControllerServiceEntity:
        """
        Enables controller service.
        """
        return nipyapi.canvas.schedule_controller(controller, True)

    def get_controller_service(self, pg: ProcessGroupEntity,
                               name: str) -> ControllerServiceEntity:
        """
        Get Controller Service by name within a given ProcessGroup.
        """
        controllers = nipyapi.canvas.list_all_controllers(pg.id, False)
        for controller in controllers:
            if controller.component.name == name:
                return controller

    def get_controller_service_type(
            self, expression: str) -> DocumentedTypeDTO:
        """
        Get Controller Service type information by type expression.
        Returns the first found controller service type.
        """
        cs_types = nipyapi.canvas.list_all_controller_types()
        for cs in cs_types:
            if expression in cs.type:
                return cs

    def get_pg_from_metric(self, metric: MetricSchema) -> ProcessGroupEntity:
        """
        Get NiFi flow (Process Group) from MetricSchema.
        """
        pg_name = self.processgroup_name(metric)
        return nipyapi.canvas.get_process_group(pg_name)

    def get_root_pg(self) -> ProcessGroupEntity:
        """
        Get the root Process Group"
        """
        return nipyapi.canvas.get_process_group("root")

    def set_polling_interval(self, pg_flow: ProcessGroupFlowEntity,
                             interval: str):
        logger.debug("Set polling interval to %s milliseconds" % interval)
        # Retrieve Polling processor
        # so far rely on "Polling" string
        http_ps = None
        for ps in pg_flow.flow.processors:
            if "Polling" in ps.status.name:
                logger.debug("Updating %s processor" % ps.status.name)
                http_ps = ps
                break
        # Enforce interval unit to miliseconds
        interval_unit = "ms"
        nipyapi.canvas.update_processor(
            http_ps,
            nipyapi.nifi.ProcessorConfigDTO(
                scheduling_period='{0}{1}'.format(interval,
                                                  interval_unit)))

    def upload_template(self, template_path: str) -> TemplateEntity:
        """
        Uploads template to root process group
        """
        # Get root PG
        root_pg = nipyapi.canvas.get_process_group("root")
        template = nipyapi.templates.upload_template(
            root_pg.id, template_path)
        return template

    def processgroup_name(self, metric: MetricSchema) -> str:
        labels = self._getQueryLabels(metric.labels)
        raw_pg_name = metric.metricname+labels
        pg_name = metric.metricname+":"+hashlib.md5(raw_pg_name.encode("utf-8")).hexdigest()
        return pg_name
    
    def _getQueryLabels(self, expression: dict) -> str:
        """
        Print Prometheus labels to make them consumable
        by Prometheus REST API.
        """
        labels = []
        for label, value in expression.items():
            labels.append("{0}='{1}'".format(label, value))

        return ",".join(labels)