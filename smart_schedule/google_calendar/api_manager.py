from oauth2client import client
import flask
import httplib2
from apiclient import discovery


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
