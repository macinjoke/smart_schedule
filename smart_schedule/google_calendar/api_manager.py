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
    engine = create_engine(db_env['database_url'])
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
    try:
        credentials = client.OAuth2Credentials.from_json(personals[0].credential)
        if credentials.access_token_expired:
            return None
        return credentials
    except IndexError:
        return None


def get_keyword_flag(user_id):
    engine = create_engine(db_env['database_url'], echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
    return personals[0].keyword_flag


def set_keyword_flag(user_id, bool):
    engine = create_engine(db_env['database_url'], echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
        personals[0].keyword_flag = bool


def get_day_flag(user_id):
    engine = create_engine(db_env['database_url'], echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
    return personals[0].day_flag


def set_day_flag(user_id, bool):
    engine = create_engine(db_env['database_url'], echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
        personals[0].day_flag = bool


def get_up_to_day_flag(user_id):
    engine = create_engine(db_env['database_url'], echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
    return personals[0].up_to_day_flag


def set_up_to_day_flag(user_id, bool):
    engine = create_engine(db_env['database_url'], echo=True)
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        personals = session.query(Personal).filter(Personal.user_id == user_id)
        personals[0].up_to_day_flag = bool


def build_service(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service


# 現在からn日分のイベントを取得
def get_n_days_events(service, n):
    now = datetime.datetime.utcnow()
    period = datetime.timedelta(days=n)
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now.isoformat() + 'Z', timeMax=(now + period).isoformat() + 'Z', maxResults=100, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events


# n日後のイベントを取得
def get_events_after_n_days(service, n):
    now = datetime.datetime.utcnow()
    days = datetime.timedelta(days=n)
    eventsResult = service.events().list(
        calendarId='primary', timeMin=(now + days).isoformat() + 'Z',
        timeMax=(now + days + datetime.timedelta(days=1)).isoformat() + 'Z',
        maxResults=100, singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events


# タイトル名で検索
def get_events_by_title(service, search_word):
    now = datetime.datetime.utcnow()
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now.isoformat() + 'Z', maxResults=100,
        singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    events = list(filter(lambda event: search_word in event['summary'], events))

    return events
