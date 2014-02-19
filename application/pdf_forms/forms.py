# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired


class PdfUploadForm(Form):

    file_field = FileField('pdf', validators=[FileRequired(),
                                              FileAllowed(['pdf'],
                                              'You can only upload pdf files')])
