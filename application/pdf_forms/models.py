# -*- coding: utf-8 -*-

from application.app import db


class Pdf(db.Model):

    __tablename__ = "pdf"

    pdf_id = db.Column(db.String(40), primary_key=True)
    name = db.Column(db.String(120))
    path = db.Column(db.String(255))
    transaction_id = db.Column(db.String(40), db.ForeignKey('transaction.transaction_id'))

    def __init__(self, pdf_id=None, name=None, path=None, transaction_id=None):
        self.pdf_id         = pdf_id
        self.name           = name
        self.path           = path
        self.transaction_id = transaction_id

    def add(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
