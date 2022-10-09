from fileinput import filename
import logging
import os
import shutil
import yaml
from typing import Optional
from xml.etree import ElementTree as et

from process_manager.nificlient import NiFiClient

from process_manager.database import (
    add_alert
)

from process_manager.models.alerts import (
    AlertModel
)

logger = logging.getLogger(__name__)

# Config catalog paths
script_dir = os.path.dirname(__file__)
TEMPLATES_PATH = os.path.join(script_dir, "catalog", "nifi", "templates/")
RULES_PATH = os.path.join(script_dir, "catalog", "alert", "rules/")

def upload_local_nifi_templates(
        nifi: NiFiClient):
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
        logger.info("Template information: {0}".format(template))


async def upload_local_alert_rules():
    """
    Upload Prometheus alert rules stored locally in the service.
    """
    # Upload alert rules
    for file in os.listdir(RULES_PATH):
        foldername = '/opt/process-manager/process_manager/prometheus-rules'
        if not os.path.isdir(RULES_PATH + file):
            logger.info("Uploading '%s' admin alert rule to Prometheus alert repository..." % file)
            try:
                file_content = open(RULES_PATH + file, 'rb')
                filename = str(file)
                fullname = os.path.join(foldername, filename)
                newfile = open(fullname, 'wb')
                shutil.copyfileobj(file_content, newfile)
            except Exception as e:
                logger.info(str(e))
                continue
            logger.info("Rule file '{0}' uploaded.".format(file))
        else:     
            subfoldername = '/opt/process-manager/process_manager/prometheus-rules/%s' % file
            for subfile in os.listdir(RULES_PATH + file):
                logger.info("Uploading '%s' admin alert rule to Prometheus alert repository..." % subfile)
                try:
                    subfile_content = open(RULES_PATH + file + '/' + subfile, 'rb')
                    rule_file = (RULES_PATH + file + '/' + "%s" % subfile)
                    subfilename = str(subfile)
                    subfullname = os.path.join(subfoldername, subfilename)
                    os.makedirs(subfoldername, exist_ok=True)
                    with open(rule_file) as singlefile:
                        try:
                            original_rule_dict = yaml.load(singlefile, Loader=yaml.FullLoader)
                            database_rule_dict = dict()
                            database_rule_dict['filename'] = subfilename.replace(".yml","")
                            database_rule_dict['rulename'] = original_rule_dict['groups'][0]['name']
                            database_rule_dict['alertname'] = original_rule_dict['groups'][0]['rules'][0]['alert']
                            database_rule_dict['expr'] = original_rule_dict['groups'][0]['rules'][0]['expr']
                            database_rule_dict['duration'] = original_rule_dict['groups'][0]['rules'][0]['for']
                            database_rule_dict['severity'] = original_rule_dict['groups'][0]['rules'][0]['labels']['severity']
                            database_rule_dict['summary'] = original_rule_dict['groups'][0]['rules'][0]['annotations']['summary']
                            database_rule_dict['description'] = original_rule_dict['groups'][0]['rules'][0]['annotations']['description']
                        except KeyError as e:
                            logger.error(str(e))
                    new_alert = await add_alert(database_rule_dict)
                    logger.info("New Alert '{0}'.".format(new_alert))
                    if new_alert:
                        # Upload Prometheus alert rule to Prometheus
                        newfile = open(subfullname, 'wb')
                        shutil.copyfileobj(subfile_content, newfile)
                except Exception as e:
                    logger.info(str(e))
                    continue
                logger.info("Rule file '{0}' uploaded.".format(subfile))


def upload_nifi_template(
                nifi: NiFiClient,
                name: str,
                file_path: str,
                description: Optional[str] = None) -> dict:
    """
    Upload NiFi templates provided by user.
    """
    logger.info("Uploading '%s' template to NiFi..." % name)
    # Update name and description of template
    tree = et.parse(file_path)
    tree.find('./name').text = name
    if description:
        tree.find('./description').text = description
    tree.write(file_path)
    # Upload template
    template = nifi.upload_template(file_path)
    # Register application information
    application_id = template.id
    TEMPLATES_PATH.replace(script_dir, "") + \
        "/%s.xml" % name
    # TEMPLATES_PATH.replace(script_dir, "") + \
    #    "/%s.xml" % application_id
    for file in os.listdir(TEMPLATES_PATH):
        logger.info("NiFi template: {0}".format(file))

    application = dict()
    application["application_id"] = application_id
    application["name"] = name
    application["description"] = description

    logger.info("Application information: {0}".format(application))
    logger.info("Template with ID '{0}' uploaded.".format(template.id))
    logger.info("Template information: {0}".format(template))

    return application