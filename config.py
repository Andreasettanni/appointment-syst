import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-12345'
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/appointment_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False