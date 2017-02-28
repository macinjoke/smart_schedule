from flask import Flask, request, abort
import flask
from flask_session import Session, SqlAlchemySessionInterface
from flask_sqlalchemy import SQLAlchemy
from oauth2client import client
import os
import uuid
import hashlib

from linebot import WebhookHandler
from linebot.exceptions import (
    InvalidSignatureError
)

from smart_schedule.settings import line_env
from smart_schedule.settings import hash_env
from smart_schedule.settings import APP_ROOT
from smart_schedule.settings import app
from smart_schedule.settings import MySession
from smart_schedule.line import event_handler
from smart_schedule.models import Personal

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
    talk_id = flask.request.args.get('talk_id')
    hash = flask.request.args.get('hash')
    if talk_id is None or hash is None:
        print(talk_id)
        print(hash)
        return 'パラメーターが不足しています'
    m = hashlib.md5()
    m.update(talk_id.encode('utf-8'))
    m.update(hash_env['seed'].encode('utf-8'))
    if hash != m.hexdigest():
        print(m.hexdigest())
        print(hash_env['seed'])
        return '不正なハッシュ値です'
    print(flask.session)
    flask.session['talk_id'] = talk_id
    print('saved session')
    print(flask.session)

    flow = client.flow_from_clientsecrets(
        os.path.join(APP_ROOT, 'client_secret.json'),
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)


@app.route('/oauth2callback')
def oauth2callback():
    print(flask.session)
    session = MySession()
    if 'talk_id' not in flask.session:
        return '不正なアクセスです。'
    talk_id = flask.session.pop('talk_id')
    flow = client.flow_from_clientsecrets(
        os.path.join(APP_ROOT, 'client_secret.json'),
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    flow.params['access_type'] = 'offline'
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    with session.begin():
        if session.query(Personal).filter(Personal.user_id == talk_id).one_or_none() is None:
            session.add(Personal(user_id=talk_id, credential=credentials.to_json()))
            return 'あなたのLineとGoogleカレンダーが正常に紐付けられました。'
        else:
            return '既にグループにGoogleアカウントが紐付けられています'


if __name__ == "__main__":
    app.run()
