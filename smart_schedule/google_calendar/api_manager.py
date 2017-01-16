from oauth2client import client
import flask
import httplib2
from apiclient import discovery
import datetime


def get_credentials():
    if 'credentials' not in flask.session:
        return False
    # TODO 本当はセッションではなくDBから読み込む
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return False
    else:
        return credentials


def build_service(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service


# 現在からn日分のイベントを取得
def get_n_days_events(service, n):
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    period = datetime.timedelta(days=n)
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, timeMax=now + period, maxResults=100, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events


# n日後のイベントを取得
def get_events_after_n_days(service, n):
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    days = datetime.timedelta(days=n)
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now + days, timeMax=now + days + datetime.timedelta(days=1),
        maxResults=100, singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events


# タイトル名で検索
def get_events_by_title(service, search_word):
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=100,
        singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    events = list(filter(lambda event: search_word in event['summary'], events))

    return events
