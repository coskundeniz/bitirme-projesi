# -*- coding: utf-8 -*-

from application.workflow.models import WorkflowState, UserWorkflow
from application.app import app

from SpiffWorkflow.storage.DictionarySerializer import DictionarySerializer
from SpiffWorkflow.storage import XmlSerializer
from SpiffWorkflow import Workflow
import xml.etree.ElementTree as ET
from subprocess import call
from uuid import uuid4
import os, re


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

def create_spec_from_xml(filename):
    """ create workflow spec from given xml file """

    serializer = XmlSerializer()

    with open(filename) as f:
        xml_data = f.read()

    wf_spec = serializer.deserialize_workflow_spec(xml_data, filename)

    return wf_spec

def generate_fdf_file(fdf_string, filename):

    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "w") as f:
        f.write(fdf_string)

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
    """ creates a workflow for database and saves on it """

    serialized_wf = workflow.serialize(serializer=DictionarySerializer())
    wf_id = str(uuid4())
    stored_wf = WorkflowState(workflow_id=wf_id,
                              workflow_name=workflow.spec.name,
                              workflow_instance=serialized_wf)
    stored_wf.add()

    # save also user_id - workflow_id to userworkflow table
    userwf = UserWorkflow(user_id=user_id, workflow_id=wf_id)
    userwf.add()

def get_workflow_instance(db_wf):

    from application.app import workflow_specs

    workflow = Workflow(workflow_specs[db_wf.workflow_name]).deserialize(DictionarySerializer(),
                                                                         db_wf.workflow_instance)
    return workflow

def get_last_workflow_id(user_id):
    """ returns id of last workflow belongs to given user """

    last_workflow = UserWorkflow.query.filter_by(user_id=user_id).all()[-1]

    return last_workflow.workflow_id

def get_form_fields(fdf_string):
    """ returns form fields as dictionary """

    pattern = re.compile(r'''
                            <<          # beginning of string
                            /T          # field name identifier
                            \((\w+)\)   # field name
                            /V          # field value identifier
                            [\(|/]      # ( or / after value identifier
                            (.+?)       # field value
                            \)?         # 0 or 1 right parenthesis
                            >>          # end of string
                            ''', re.VERBOSE)

    fields = pattern.findall(fdf_string)

    form_fields = {}

    for field_name, field_value in fields:
        form_fields.update({field_name: field_value})

    return form_fields

def get_all_specs():
    """ returns a dictionary consists of workflow name - spec pairs """

    from application.app import config_data

    return {wf_config["name"]: create_spec_from_xml(wf_config["spec_file"])
            for wf_config in config_data}

