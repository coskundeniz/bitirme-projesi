# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for
from flask import request, g, send_from_directory, flash
from flask.ext.login import login_required
from werkzeug import secure_filename

from application.app import app, db
from application.pdf_forms.forms import PdfUploadForm
from application.pdf_forms.models import Pdf
from application.users.models import User, Transaction
from application.workflow.models import WorkflowState
from application.utils import generate_fdf_file, generate_output_pdf
from application.utils import get_workflow_instance, get_from_config

from SpiffWorkflow.storage.DictionarySerializer import DictionarySerializer
from SpiffWorkflow import Task
from uuid import uuid4
from datetime import datetime
import os


mod = Blueprint('forms', __name__)


@mod.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():

    form = PdfUploadForm()
    if form.validate_on_submit():

        filename = secure_filename(form.file_field.data.filename)
        file_path = app.config['UPLOAD_FOLDER']

        # save file to uploads folder
        form.file_field.file.save(os.path.join(file_path, filename))

        # add file to database if not exists
        pdf_exists = Pdf.query.filter_by(name=filename).first()
        if not pdf_exists:
            uploaded_file = Pdf(pdf_id=str(uuid4()), name=filename, path=file_path)
            uploaded_file.add()

            return redirect(url_for('users.user_page', username=g.user.username))
        else:
            flash("A pdf form with same name already exists")

    return render_template('upload.html', form=form)

@mod.route('/get_data_as_html', methods=['GET', 'POST'])
def get_form_data():

    field_str = {}
    field_names = {}

    for key, value in request.form.iteritems():
        if key is "submit":
            pass
        elif key.startswith("str_"):
            field_str[key] = value
        else:
            field_names[key] = value

    # create list of tuples to send forge_fdf as parameter
    str_fields = list(tuple(field_str.iteritems()))
    name_fields = list(tuple(field_names.iteritems()))

    transaction_id = str(uuid4())

    fdf_file = transaction_id + ".fdf"
    generate_fdf_file(str_fields, name_fields, fdf_file)

    # get workflow and complete send_request_form task
    db_wf = WorkflowState.query.filter_by(user_id=g.user.id).first()
    workflow = get_workflow_instance(get_from_config(db_wf.workflow_name, "spec_file"), db_wf)

    send_request_task = workflow.get_tasks(state=Task.READY)[0]
    workflow.complete_task_from_id(send_request_task.id)
    #workflow.task_tree.dump()

    generate_output_pdf(transaction_id, send_request_task)

    # update workflow on database
    serialized_wf = workflow.serialize(serializer=DictionarySerializer())
    db_wf.workflow_instance = serialized_wf

    instructor = User.query.filter_by(username=request.form["str_instructor"]).first()
    db_wf.instructor_id = instructor.id

    db.session.commit()

    # create transaction and add to database
    transaction = Transaction(transaction_id, datetime.now(), db_wf.workflow_id)
    transaction.add()

    # create pdf object for database and add
    filename = transaction_id + ".pdf"
    output_pdf = Pdf(str(uuid4()), filename, app.config['UPLOAD_FOLDER'], transaction_id)
    output_pdf.add()

    return redirect(url_for('users.user_page', username=g.user.username))

@mod.route('/show_pdf/<filename>')
@login_required
def show_pdf(filename):
    """ get pdf from database and show """

    pdf = Pdf.query.filter_by(name=filename).first_or_404()
    return send_from_directory(pdf.path, pdf.name)

@mod.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
