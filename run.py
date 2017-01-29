from flask import Flask, request, abort
import flask
from oauth2client import client
import os
import uuid
import hashlib

from linebot import WebhookHandler
from linebot.exceptions import (
    InvalidSignatureError
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from smart_schedule.settings import line_env
from smart_schedule.settings import db_env
from smart_schedule.settings import hash_env
from smart_schedule.settings import APP_ROOT
from smart_schedule.line import event_handler
from smart_schedule.models import Personal

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
app.config['SESSION_REFRESH_EACH_REQUEST'] = False

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
    response = 'Hello, Smart Schedule'
    return response


@app.route('/oauth2')
def oauth2():
    flow = client.flow_from_clientsecrets(
        os.path.join(APP_ROOT, 'client_secret.json'),
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    user_id = flask.request.args.get('user_id')
    hash = flask.request.args.get('hash')
    if user_id is None or hash is None:
        print(user_id)
        print(hash)
        return 'パラメーターが不足しています'
    m = hashlib.md5()
    m.update(user_id.encode('utf-8'))
    m.update(hash_env['seed'].encode('utf-8'))
    if hash != m.hexdigest():
        print(m.hexdigest())
        print(hash_env['seed'])
        return '不正なハッシュ値です'
    print(flask.session)
    flask.session['user_id'] = user_id
    print('saved session')
    print(flask.session)

    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)


@app.route('/oauth2callback')
def oauth2callback():
    print(flask.session)
    if 'user_id' not in flask.session:
        return '不正なアクセスです。'
    user_id = flask.session['user_id']
    flask.session.pop('user_id')
    flow = client.flow_from_clientsecrets(
        os.path.join(APP_ROOT, 'client_secret.json'),
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    engine = create_engine(db_env['database_url'])
    session = sessionmaker(bind=engine, autocommit=True)()
    with session.begin():
        session.add(Personal(user_id=user_id, credential=credentials.to_json()))
    return 'あなたのLineとGoogleカレンダーが正常に紐付けられました。'


if __name__ == "__main__":
    app.run()
