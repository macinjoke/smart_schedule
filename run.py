from flask import Flask, request, abort
import flask
from oauth2client import client
import os
import uuid

from linebot import WebhookHandler
from linebot.exceptions import (
    InvalidSignatureError
)

from smart_schedule.settings import line_env
from smart_schedule.settings import APP_ROOT
from smart_schedule.line import event_handler
from smart_schedule.google_calendar import api_manager

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())

handler = WebhookHandler(line_env['channel_secret'])


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        event_handler.handle(handler, body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@app.route('/')
def index():
    credentials = api_manager.get_credentials()
    if credentials is False:
        return flask.redirect(flask.url_for('oauth2callback'))
    response = '認証が完了しました。Smart Schedule でGoogle Calendarにアクセスできます。'

    return response


@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets(
        os.path.join(APP_ROOT, 'client_secret.json'),
        scope = 'https://www.googleapis.com/auth/calendar',
        redirect_uri = flask.url_for('oauth2callback', _external=True))
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        # TODO 本当はセッションではなくDBに入れる
        flask.session['credentials'] = credentials.to_json()
        return flask.redirect(flask.url_for('index'))
