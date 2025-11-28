from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Regulation(db.Model):
    __tablename__ = 'regulations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

class Upload(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    regulation_id = db.Column(db.Integer, db.ForeignKey('regulations.id'), nullable=False)
    old_path = db.Column(db.Text)
    new_path = db.Column(db.Text)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

class Summary(db.Model):
    __tablename__ = 'summaries'
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('uploads.id'), nullable=False)
    old_summary = db.Column(db.Text)
    new_summary = db.Column(db.Text)

class EntityGraph(db.Model):
    __tablename__ = 'entity_graphs'
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('uploads.id'), nullable=False)
    old_json = db.Column(db.Text)
    new_json = db.Column(db.Text)
    graph_old = db.Column(db.Text)
    graph_new = db.Column(db.Text)
