from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    crimes = db.relationship('Crime', backref='reporter', lazy=True)
    thefts = db.relationship('Theft', backref='victim', lazy=True)
    

class Register(db.Model, UserMixin):
    idno = db.Column(db.Integer, primary_key=True, nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    phonenumber = db.Column(db.String(20), nullable=False)
    residence = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    