import logging
import time
import hashlib
import os
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
    MetricModel
)
from telemetry_orchestrator.server.models.ue_location import (
    UELocationModel
)

logger = logging.getLogger(__name__)

EXPORTER_SERVICE_PG_NAME = "exporter-service"

NIFI_URI = os.getenv("NIFI_URI")


class NiFiClient(object):
    """
    Class encapsulating the main operations with Apache NiFi.
    """

    def __init__(self,
                 username: str,
                 password: str,
                 url: str = str(NIFI_URI)):

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
        the create_parameter_context method.
        """
        param_entities = []
        for key, value in params.items():
            if key == "request_password" or key == "cert_password":
                param = nifi_params.prepare_parameter(key, value, sensitive=True)
            else:
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
        logger.info("Get parameter list %s" % param_entities)
        logger.info("Get PG ID %s" % pg.id)
        context = nifi_params.create_parameter_context(
            pg.id, parameters=param_entities)
        nifi_params.assign_context_to_process_group(pg, context.id)
        return context
    
    def update_parameter_context(
            self, pg: ProcessGroupEntity,
            params: dict) -> ParameterContextEntity:
        """
        Update parameter context from a given dictionary.
        The context is assigned to the specified process group (by ID).
        """
        # param_entities = self.prepare_parameters_for_context(params)

        nifi_params.remove_context_from_process_group(pg)
        original_context = nifi_params.get_parameter_context(
             identifier=pg.id, identifier_type='name', greedy=True)
        nifi_params.delete_parameter_context(original_context, refresh=True)
        new_context = self.set_parameter_context(pg, params)
        nifi_params.assign_context_to_process_group(pg, new_context.id)
        return new_context

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

    def delete_flow_from_metric(self, metric: MetricModel, metric_id: str):
        """
        Delete MetricModel flow.
        """
        # Stop process group
        metric_pg = self.stop_flow_from_metric(metric, metric_id)
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
        pg_name = metric.metricname+":"+metric_id 
        logger.debug("'{0}' flow deleted in NiFi.".format(pg_name))

    def delete_flow_from_ue_location(self, ue_location: UELocationModel, ue_location_id: str):
        """
        Delete UELocationModel flow.
        """
        # Stop process group
        ue_location_pg = self.stop_flow_from_ue_location(ue_location, ue_location_id)
        # Disable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(
            ue_location_pg.id, False)
        if controllers:
            for controller in controllers:
                if controller.status.run_status == 'ENABLED':
                    logger.debug("Disabling controller %s ..."
                                 % controller.component.name)
                    nipyapi.canvas.schedule_controller(
                        controller, False, True)
        # Delete UE Location PG
        nipyapi.canvas.delete_process_group(ue_location_pg, True)
        pg_name = "ue_location"+":"+ue_location_id 
        logger.debug("'{0}' flow deleted in NiFi.".format(pg_name))

    def update_flow_from_metric(self, newmetric: MetricModel,
                                metric_id: str, 
                                args: dict) -> ProcessGroupEntity:
        """
        Stops flow, updates variables and re-starts flow
        for a given MetricModel.
        """
        # Stop process group
        metric_pg = self.stop_flow_from_metric(newmetric, metric_id)
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
        
        logger.debug("Update with arguments %s" % args)
        # Set Parameter Context for Metric PG
        self.update_parameter_context(metric_pg, args)

        # Hack to support scheduling for a given processor
        metric_pg_flow = nipyapi.canvas.get_flow(
            metric_pg.id).process_group_flow
        if "interval" in args:
            self.set_polling_interval(metric_pg_flow, args["interval"])
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

        # Restart and schedule PG
        self.start_flow_from_metric(newmetric, metric_id)
        pg_name = newmetric.metricname+":"+metric_id 
        logger.debug(
            "'{0}' flow updated and scheduled in NiFi.".format(pg_name))

        return metric_pg   

    def update_flow_from_ue_location(self, new_ue_location: UELocationModel,
                                ue_location_id: str, 
                                args: dict) -> ProcessGroupEntity:
        """
        Stops flow, updates variables and re-starts flow
        for a given UELocationModel.
        """
        # Stop process group
        ue_location_pg = self.stop_flow_from_ue_location(new_ue_location, ue_location_id)
        # Disable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(
            ue_location_pg.id, False)
        if controllers:
            for controller in controllers:
                if controller.status.run_status == 'ENABLED':
                    logger.debug("Disabling controller %s ..."
                                 % controller.component.name)
                    nipyapi.canvas.schedule_controller(
                        controller, False, True)
        
        logger.debug("Update with arguments %s" % args)
        # Set Parameter Context for UE Location PG
        self.update_parameter_context(ue_location_pg, args)

        # Hack to support scheduling for a given processor
        ue_location_pg_flow = nipyapi.canvas.get_flow(
            ue_location_pg.id).process_group_flow
        if "interval" in args:
            self.set_polling_interval(ue_location_pg_flow, args["interval"])
        # Enable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(ue_location_pg.id, False)
        if controllers:
            # Enable controller services
            # Start with the registry controller
            for controller in controllers:
                logger.debug(
                    "Enabling controller %s ..."
                    % controller.component.name)
                if controller.status.run_status != 'ENABLED':
                    nipyapi.canvas.schedule_controller(controller, True)

        # Restart and schedule PG
        self.start_flow_from_ue_location(new_ue_location, ue_location_id)
        pg_name = "ue_location"+":"+ue_location_id 
        logger.debug(
            "'{0}' flow updated and scheduled in NiFi.".format(pg_name))

        return ue_location_pg   

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

    def deploy_flow_from_metric(self, metric: MetricModel, 
                                metric_id: str,
                                application_name: str,
                                args: dict) -> ProcessGroupEntity:
        """
        Deploys a NiFi template
        from a passed MetricModel model.
        """
        # Get root PG
        root_pg = nipyapi.canvas.get_process_group("root")
        # Place the PG in a random location in canvas
        location_x = randrange(0, 4000)
        location_y = randrange(0, 4000)
        location = (location_x, location_y)
        pg_name = metric.metricname+":"+metric_id 
        metric_pg = nipyapi.canvas.create_process_group(
            root_pg, pg_name, location
        )
        logger.debug("Deploy with arguments %s" % args)
        # Set Parameter Context for Metric PG
        self.set_parameter_context(metric_pg, args)

        # Deploy Metric template
        metric_template = nipyapi.templates.get_template_by_name(
            application_name)
        metric_pg_flow = nipyapi.templates.deploy_template(
            metric_pg.id,
            metric_template.id,
            -250, 200)

        http_processor = None
        for processor in metric_pg_flow.flow.processors:
            if "Polling" in processor.status.name:
                http_processor = processor
                processor_properties = processor.component.config.properties
                logger.info("'{0}' NiFi processor properties.".format(processor_properties))
                if 'Basic Authentication Password' in processor_properties:
                    processor_properties['Basic Authentication Password'] = args['request_password']
                    logger.info("'{0}' NiFi processor properties.".format(processor_properties))
                    #time.sleep(1)
                    nipyapi.canvas.update_processor(processor=http_processor, update=nipyapi.nifi.ProcessorConfigDTO(properties=processor_properties))
                    #time.sleep(1)

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
                    properties = controller.component.properties
                    logger.info("'{0}' NiFi controller properties.".format(properties))
                    if 'Truststore Password' in properties:
                        properties['Truststore Password'] = args['cert_password']
                        logger.info("'{0}' NiFi controller properties.".format(properties))
                        #time.sleep(1)
                        nipyapi.canvas.update_controller(controller=controller, update=nipyapi.nifi.ControllerServiceDTO(properties=properties))
                        #time.sleep(1)
                    nipyapi.canvas.schedule_controller(controller=controller, scheduled=True, refresh=True)
        
        # Hack to support scheduling for a given processor
        if "interval" in args:
            self.set_polling_interval(metric_pg_flow, args["interval"])

        logger.debug("'{0}' flow deployed in NiFi.".format(pg_name))
        return metric_pg

    def deploy_flow_from_ue_location(self, ue_location: UELocationModel, 
                                ue_location_id: str,
                                application_name: str,
                                args: dict) -> ProcessGroupEntity:
        """
        Deploys a NiFi template
        from a passed UELocationModel model.
        """
        # Get root PG
        root_pg = nipyapi.canvas.get_process_group("root")
        # Place the PG in a random location in canvas
        location_x = randrange(0, 4000)
        location_y = randrange(0, 4000)
        location = (location_x, location_y)
        pg_name = "ue_location"+":"+ue_location_id 
        ue_location_pg = nipyapi.canvas.create_process_group(
            root_pg, pg_name, location
        )
        logger.info("Get PG id %s" % ue_location_pg.id)
        logger.debug("Deploy with arguments %s" % args)
        # Set Parameter Context for UELocation PG
        self.set_parameter_context(ue_location_pg, args)

        # Deploy UELocation template
        ue_location_template = nipyapi.templates.get_template_by_name(
            application_name)
        ue_location_pg_flow = nipyapi.templates.deploy_template(
            ue_location_pg.id,
            ue_location_template.id,
            -250, 200)

        # Set Parameter Context and enable controller services (if any) for all derived Process Grups
        process_groups = nipyapi.canvas.list_all_process_groups(ue_location_pg.id)
        if process_groups:
            logger.info("Get process groups list length %s" % len(process_groups))
            for process_group in process_groups:
                if process_group.id != ue_location_pg.id or process_group.id == ue_location_pg.id:
                    logger.info("Get process group id %s" % process_group.id)
                    if process_group.id != ue_location_pg.id:
                        self.set_parameter_context(process_group, args)
                    process_group_entity = nipyapi.canvas.get_flow(process_group.id)
                    
                    # Hack to support scheduling for a given processor
                    if "cred_interval" in args and "poll_interval" in args:
                        logger.info("Get cred_interval arg %s" % args["cred_interval"])
                        logger.info("Get poll_interval arg %s" % args["poll_interval"])
                        self.set_credentials_interval(process_group_entity.process_group_flow, args["cred_interval"])
                        self.set_polling_interval(process_group_entity.process_group_flow, args["poll_interval"])
                        
                    # Enable controller services (if any)
                    controllers = nipyapi.canvas.list_all_controllers(process_group.id, False)
                    if controllers:
                        # Enable controller services
                        # Start with the registry controller
                        for controller in controllers:
                            logger.debug(
                                "Enabling controller %s ..."
                                % controller.component.name)
                            if controller.status.run_status != 'ENABLED':
                                nipyapi.canvas.schedule_controller(controller, True)
        
        # Enable controller services (if any)
        controllers = nipyapi.canvas.list_all_controllers(ue_location_pg.id, False)
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
            logger.info("Get args %s" % args["interval"])
            self.set_polling_interval(ue_location_pg_flow, args["interval"])

        logger.debug("'{0}' flow deployed in NiFi.".format(pg_name))
        return ue_location_pg


    def instantiate_flow_from_metric(self, metric: MetricModel, 
                                     metric_id: str,
                                     application_name: str,
                                     args: dict) -> ProcessGroupEntity:
        """
        Deploys and starts NiFi template given a MetricModel.
        """
        metric_pg = self.deploy_flow_from_metric(
            metric, metric_id, application_name, args)
        # Schedule PG
        nipyapi.canvas.schedule_process_group(metric_pg.id, True)
        pg_name = metric.metricname+":"+metric_id 
        logger.debug(
            "'{0}' flow scheduled in NiFi.".format(pg_name))
        return metric_pg   

    def instantiate_flow_from_ue_location(self, ue_location: UELocationModel, 
                                     ue_location_id: str,
                                     application_name: str,
                                     args: dict) -> ProcessGroupEntity:
        """
        Deploys and starts NiFi template given a UELocationModel.
        """
        ue_location_pg = self.deploy_flow_from_ue_location(
            ue_location, ue_location_id, application_name, args)
        # Schedule PG
        nipyapi.canvas.schedule_process_group(ue_location_pg.id, True)
        pg_name = "ue_location"+":"+ue_location_id 
        logger.debug(
            "'{0}' flow scheduled in NiFi.".format(pg_name))
        return ue_location_pg 

    def start_flow_from_metric(self, 
                               metric: MetricModel,
                               metric_id: str) -> ProcessGroupEntity:
        """
        Starts NiFi flow given a MetricModel.
        """
        # Schedule PG
        pg_name = metric.metricname+":"+metric_id 
        metric_pg = nipyapi.canvas.get_process_group(pg_name)
        nipyapi.canvas.schedule_process_group(metric_pg.id, True)
        logger.debug(
            "'{0}' flow scheduled in NiFi.".format(pg_name))
        return metric_pg

    def start_flow_from_ue_location(self, 
                               ue_location: UELocationModel,
                               ue_location_id: str) -> ProcessGroupEntity:
        """
        Starts NiFi flow given a UELocationModel.
        """
        # Schedule PG
        pg_name = "ue_location"+":"+ue_location_id 
        ue_location_pg = nipyapi.canvas.get_process_group(pg_name)
        nipyapi.canvas.schedule_process_group(ue_location_pg.id, True)
        logger.debug(
            "'{0}' flow scheduled in NiFi.".format(pg_name))
        return ue_location_pg

    def stop_flow_from_metric(self, 
                              metric: MetricModel, 
                              metric_id: str) -> ProcessGroupEntity:
        """
        Stop NiFi flow (Process Group) from MetricModel.
        """
        pg_name = metric.metricname+":"+metric_id
        metric_pg = nipyapi.canvas.get_process_group(pg_name)
        nipyapi.canvas.schedule_process_group(metric_pg.id, False)
        logger.debug(
            "'{0}' flow unscheduled in NiFi.".format(pg_name))
        return metric_pg


    def stop_flow_from_ue_location(self, 
                              ue_location: UELocationModel, 
                              ue_location_id: str) -> ProcessGroupEntity:
        """
        Stop NiFi flow (Process Group) from UELocationModel.
        """
        pg_name = "ue_location"+":"+ue_location_id
        ue_location_pg = nipyapi.canvas.get_process_group(pg_name)
        nipyapi.canvas.schedule_process_group(ue_location_pg.id, False)
        logger.debug(
            "'{0}' flow unscheduled in NiFi.".format(pg_name))
        return ue_location_pg

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

    def get_pg_from_metric(self, metric: MetricModel) -> ProcessGroupEntity:
        """
        Get NiFi flow (Process Group) from MetricModel.
        """
        pg_name = self.processgroup_name(metric)
        return nipyapi.canvas.get_process_group(pg_name)

    def get_pg_from_ue_location(self, ue_location: UELocationModel) -> ProcessGroupEntity:
        """
        Get NiFi flow (Process Group) from UELocationModel.
        """
        pg_name = self.processgroup_name(ue_location)
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
        polling_processor = False
        http_ps = None
        for ps in pg_flow.flow.processors:
            if "PollingGetToken" in ps.status.name:
                logger.debug("Updating %s processor" % ps.status.name)
                http_ps = ps
                polling_processor = True
                break
        
        if polling_processor == True:
            # Enforce interval unit to miliseconds
            interval_unit = "ms"
            nipyapi.canvas.update_processor(
                http_ps,
                nipyapi.nifi.ProcessorConfigDTO(
                    scheduling_period='{0}{1}'.format(interval,
                                                    interval_unit)))

    def set_credentials_interval(self, pg_flow: ProcessGroupFlowEntity,
                             interval: str):
        logger.debug("Set credentials interval to %s milliseconds" % interval)
        # Retrieve GetCredentials processor
        # so far rely on "GetCredentials" string
        credentials_processor = False
        http_ps = None
        for ps in pg_flow.flow.processors:
            if "GetCredentials" in ps.status.name:
                logger.debug("Updating %s processor" % ps.status.name)
                http_ps = ps
                credentials_processor = True
                break
        
        if credentials_processor == True:
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

    def processgroup_name(self, metric: MetricModel) -> str:
        """
        DEPRECATED:
        Generation of PG name from the hash composed of the metric along 
        with its own tags
        """
        labels = self._getQueryLabels(metric.labels)
        raw_pg_name = metric.metricname+labels
        pg_name = metric.metricname+":"+hashlib.md5(
            raw_pg_name.encode("utf-8")).hexdigest()
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