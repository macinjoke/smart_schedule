from oauth2client import client
import flask
import httplib2
from apiclient import discovery
import datetime

from smart_schedule.models import Personal
from smart_schedule.settings import MySession


def get_credentials(talk_id):
    session = MySession()
    with session.begin() as s:
        personals = session.query(Personal).filter(Personal.user_id == talk_id)
        try:
            credentials = client.OAuth2Credentials.from_json(personals[0].credential)
            if credentials.access_token_expired:
                print('認証の期限が切れています')
                http = credentials.authorize(httplib2.Http())
                credentials.refresh(http)
                print('リフレッシュしました')
                personal = session.query(Personal).filter_by(user_id=talk_id).one()
                personal.credential = credentials.to_json()
                print('新しい認証情報をDBに保存しました')
                return credentials
            return credentials
        except IndexError:
            return None


def build_service(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service


# 現在からn日分のイベントを取得
def get_n_days_events(service, calendar_id, n):
    now = datetime.datetime.utcnow()
    period = datetime.timedelta(days=n)
    eventsResult = service.events().list(
        calendarId=calendar_id, timeMin=now.isoformat() + 'Z', timeMax=(now + period).isoformat() + 'Z', maxResults=100, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events


# n日後のイベントを取得
def get_events_after_n_days(service, calendar_id, n):
    now = datetime.datetime.utcnow()
    days = datetime.timedelta(days=n)
    eventsResult = service.events().list(
        calendarId=calendar_id, timeMin=(now + days).isoformat() + 'Z',
        timeMax=(now + days + datetime.timedelta(days=1)).isoformat() + 'Z',
        maxResults=100, singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events


# タイトル名で検索
def get_events_by_title(service, calendar_id, search_word):
    now = datetime.datetime.utcnow()
    eventsResult = service.events().list(
        calendarId=calendar_id, timeMin=now.isoformat() + 'Z', maxResults=100,
        singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    events = list(filter(lambda event: search_word in event['summary'], events))

    return events


# イベントを作成
def create_event(service, calendar_id, date, title):
    event_data = {
        'summary': title,
        'description': 'generated by Smart Schedule',
        'start': {
            'date': '{}-{}-{}'.format(date.year, date.month, date.day),
            'timeZone': 'Asia/Tokyo',
        },
        'end': {
            'date': '{}-{}-{}'.format(date.year, date.month, date.day),
            'timeZone': 'Asia/Tokyo',
        }
    }

    event = service.events().insert(calendarId=calendar_id, body=event_data).execute()
    return event


def get_calendar_list(service):
    calendar_list = service.calendarList().list().execute()
    return calendar_list
