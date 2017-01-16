from oauth2client import client
import flask
import httplib2
from apiclient import discovery
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from smart_schedule.models import Personal
from smart_schedule.settings import db_env


def get_credentials(user_id):
    engine = create_engine(db_env['database_url'], echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
    print('personals')
    print(personals)
    try:
        credentials = client.OAuth2Credentials.from_json(personals[0].credential)
        if credentials.access_token_expired:
            return False
        return credentials
    except IndexError:
        return False


def build_service(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service
