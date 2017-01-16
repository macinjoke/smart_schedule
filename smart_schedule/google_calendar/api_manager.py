from oauth2client import client
import flask
import httplib2
from apiclient import discovery
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from smart_schedule.models import Personal


def get_credentials(user_id):
    engine = create_engine('postgresql://makinoshunni@localhost:5432/smart_schedule', echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personal = session.query(Personal).filter(Personal.user_id == user_id)
    credentials = client.OAuth2Credentials.from_json(personal.credential)
    if credentials.access_token_expired:
        return False
    else:
        return credentials


def build_service(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service
