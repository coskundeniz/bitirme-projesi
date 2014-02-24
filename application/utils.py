# -*- coding: utf-8 -*-

from application.workflow.models import WorkflowState
from application.app import app

from SpiffWorkflow.storage.DictionarySerializer import DictionarySerializer
from SpiffWorkflow.storage import XmlSerializer
from SpiffWorkflow import Workflow
import xml.etree.ElementTree as ET
from fdfgen import forge_fdf
from subprocess import call
from uuid import uuid4
import os


def get_config_data():
    """ get config data from xml file """

    xml_tree = ET.parse("wf_config.xml")
    root = xml_tree.getroot()

    # find all elements which have workflow tag
    workflows = root.findall('workflow')

    config_data_list = []

    # make dictionary from workflow elements and add to list
    for workflow in workflows:
        workflow_dict = {}
        workflow_dict["name"] = workflow.find('name').text
        workflow_dict["spec_file"] = workflow.find('spec_file').text

        config_data_list.append(workflow_dict)

    return config_data_list

def get_from_config(workflow_name, field_name):
    """ returns the value of a specific field for a workflow in wf_config """

    from application.app import config_data

    for item in config_data:
        if item["name"] == workflow_name:
            return item.get(field_name, None)

def create_spec_from_xml(filename=None):
    """ create workflow spec from given xml file """

    serializer = XmlSerializer()

    with open(filename) as f:
        xml_data = f.read()

    wf_spec = serializer.deserialize_workflow_spec(xml_data, filename)

    return wf_spec

def generate_fdf_file(str_fields, name_fields, filename):

    fdf_string = forge_fdf("",
                           fdf_data_strings=str_fields,
                           fdf_data_names=name_fields)

    fdf_file = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "w")
    fdf_file.write(fdf_string)
    fdf_file.close()

def generate_output_pdf(transaction_id, current_task, flatten=False):
    """ merge fdf to pdf to create output pdf """

    file_name = transaction_id + ".pdf"
    fdf_file = transaction_id + ".fdf"
    output_file = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

    form_name = current_task.get_spec_data("pdf_form")

    if flatten:
        call(["pdftk",
            os.path.join(app.config["UPLOAD_FOLDER"], form_name),
            "fill_form",
            os.path.join(app.config['UPLOAD_FOLDER'], fdf_file),
            "output",
            output_file,
            "flatten"])
    else:
        call(["pdftk",
            os.path.join(app.config["UPLOAD_FOLDER"], form_name),
            "fill_form",
            os.path.join(app.config['UPLOAD_FOLDER'], fdf_file),
            "output",
            output_file])

def save_workflow_instance(workflow, user_id=None, instructor_id=None):

    serialized_wf = workflow.serialize(serializer=DictionarySerializer())
    stored_wf = WorkflowState(workflow_id=str(uuid4()),
                              workflow_name=workflow.spec.name,
                              workflow_instance=serialized_wf,
                              user_id=user_id,
                              instructor_id=instructor_id)
    stored_wf.add()

def get_workflow_instance(filename, db_wf):

    workflow = Workflow(create_spec_from_xml(filename)).deserialize(DictionarySerializer(),
                                                                    db_wf.workflow_instance)
    return workflow