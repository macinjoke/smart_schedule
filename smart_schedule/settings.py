import os
import uuid
from datetime import timedelta
import yaml

from dotenv import load_dotenv
from flask import Flask
from flask_session import Session
from smart_schedule.models import db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


APP_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, '..'))
REFRESH_ERROR = 'REFRESH_ERROR'

messages_file = os.path.join(PROJECT_ROOT, 'messages/line_bot.yml')
with open(messages_file) as f:
    messages = yaml.load(f)

dotenv_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

google_env = {
    'client_id': os.environ.get('CLIENT_ID'),
    'client_secret': os.environ.get('CLIENT_SECRET'),
    'redirect_uri': os.environ.get('REDIRECT_URI'),
}

line_env = {
    'channel_access_token': os.environ.get('CHANNEL_ACCESS_TOKEN'),
    'channel_secret': os.environ.get('CHANNEL_SECRET'),
    'user_id': os.environ.get("LINE_USER_ID"),
    'time_out_seconds': os.environ.get("TIME_OUT_SECONDS")
}

db_env = {
    'database_url': os.environ.get('DATABASE_URL')
}

web_env = {
    'host': os.environ.get('WEB_SERVER_HOST')
}

hash_env = {
    'seed': os.environ.get('HASH_SEED')
}

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = db_env['database_url']
app.config['SQLALCHEMY_NATIVE_UNICODE'] = 'utf-8'
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
app.config['SESSION_KEY_PREFIX'] = 'user'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
Session(app)
db.init_app(app)
db.app = app

engine = create_engine(db_env['database_url'])
MySession = sessionmaker(bind=engine, autocommit=True)
