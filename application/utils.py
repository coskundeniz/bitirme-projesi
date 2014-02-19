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
        workflow_dict["begin_form"] = workflow.find('begin_form').text

        config_data_list.append(workflow_dict)

    return config_data_list

def create_spec_from_xml(filename=None):
    """ create workflow spec from given xml file """

    serializer = XmlSerializer()

    with open(filename) as f:
        xml_data = f.read()

    wf_spec = serializer.deserialize_workflow_spec(xml_data, filename)

    return wf_spec


class Status(object):
    """ states for entire workflow

    abbreviations:
        rf: request form
        pp: project plan
        mr: mid report
        lr: last report
        wa: waiting approval

    """

    INITIAL      = "initial"
    STARTED      = "started"
    RF_DRAFT     = "request form draft"
    RF_WA        = "request form waiting approval"
    RF_APPROVED  = "request form approved"
    PP_DRAFT     = "project plan draft"
    PP_WA        = "project plan waiting approval"
    PP_APPROVED  = "project plan approved"
    MR_DRAFT     = "mid report draft"
    MR_WA        = "mid report waiting approval"
    MR_APPROVED  = "mid report approved"
    LR_DRAFT     = "last report draft"
    LR_WA        = "last report waiting approval"
    LR_APPROVED  = "last report approved"
    FINISHED     = "finished"

def next_status(current_status=Status.INITIAL, action=None):

    if(current_status == Status.INITIAL and action == "start"):
        return Status.STARTED

    elif((current_status == Status.STARTED and action == "request_form") or
         (current_status == Status.RF_WA and action == "reject_request_form")):
        return Status.RF_DRAFT
    elif(current_status == Status.RF_DRAFT and action == "submit_request_form"):
        return Status.RF_WA
    elif(current_status == Status.RF_WA and action == "approve_request_form"):
        return Status.RF_APPROVED

    elif((current_status == Status.RF_APPROVED and action == "project_plan") or
         (current_status == Status.PP_WA and action == "reject_project_plan")):
        return Status.PP_DRAFT
    elif(current_status == Status.PP_DRAFT and action == "submit_project_plan"):
        return Status.PP_WA
    elif(current_status == Status.PP_WA and action == "approve_project_plan"):
        return Status.PP_APPROVED

    elif((current_status == Status.PP_APPROVED and action == "mid_report") or
         (current_status == Status.MR_WA and action == "reject_mid_report")):
        return Status.MR_DRAFT
    elif(current_status == Status.MR_DRAFT and action == "submit_mid_report"):
        return Status.MR_WA
    elif(current_status == Status.MR_WA and action == "approve_mid_report"):
        return Status.MR_APPROVED

    elif((current_status == Status.MR_APPROVED and action == "last_report") or
         (current_status == Status.LR_WA and action == "reject_last_report")):
        return Status.LR_DRAFT
    elif(current_status == Status.LR_DRAFT and action == "submit_last_report"):
        return Status.LR_WA
    elif(current_status == Status.LR_WA and action == "approve_last_report"):
        return Status.LR_APPROVED

    elif(current_status == Status.LR_APPROVED and action == "finish"):
        return Status.FINISHED
    else:
        return "Unknown action"

def generate_fdf_file(str_fields, name_fields, filename):

    fdf_string = forge_fdf("",
                           fdf_data_strings=str_fields,
                           fdf_data_names=name_fields)

    fdf_file = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "w")
    fdf_file.write(fdf_string)
    fdf_file.close()

def generate_output_pdf(transaction_id, flatten=False):
    """ merge fdf to pdf to create output pdf """

    file_name = transaction_id + ".pdf"
    fdf_file = transaction_id + ".fdf"
    output_file = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

    for workflow in get_config_data():
        if workflow["name"] == "Bitirme":
            form_name = workflow["begin_form"]

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
                              workflow_instance=serialized_wf,
                              user_id=user_id,
                              instructor_id=instructor_id)
    stored_wf.add()

def get_workflow_instance(filename, db_wf):

    workflow = Workflow(create_spec_from_xml(filename)).deserialize(DictionarySerializer(),
                                                                    db_wf.workflow_instance)
    return workflow