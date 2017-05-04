from datetime import datetime
import flask
import urllib
import hashlib
import re
from linebot.models import TextSendMessage
from linebot import LineBotApi
from smart_schedule.settings import (
    line_env, web_env, hash_env
)
line_bot_api = LineBotApi(line_env['channel_access_token'])

# TODO 以降の関数たちはどこにあるべきか、リファクタリングの余地が無いか考える

def reply_google_auth_message(event):
    auth_url = flask.url_for('oauth2')
    if event.source.type == 'user':
        talk_id = event.source.user_id
    elif event.source.type == 'group':
        talk_id = event.source.group_id
    elif event.source.type == 'room':
        talk_id = event.source.room_id
    else:
        raise Exception('invalid `event.source`')
    m = hashlib.md5()
    m.update(talk_id.encode('utf-8'))
    m.update(hash_env['seed'].encode('utf-8'))
    params = urllib.parse.urlencode({'talk_id': talk_id, 'hash': m.hexdigest()})
    url = '{}{}?{}'.format(web_env['host'], auth_url, params)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='このリンクから認証を行ってください\n{}'.format(url))
    )


def reply_refresh_error_message(event):
    reply_text = '''認証情報の更新エラーが発生しました。同じGoogleアカウントで複数の\
認証を行っている場合にこの不具合が発生します。このトークでSmart Scheduleを使用したい場合\
は以下のいずれかを行った後で認証しなおしてください。

1. 同じアカウントで認証しているトークでlogoutコマンドを行う(オススメ)

2. 下記URLから手動でSmart Scheduleの認証を解除する\
 https://myaccount.google.com/u/1/permissions'''
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


def reply_invalid_credential_error_message(event):
    reply_text = '''無効な認証情報です。同じGoogleアカウントで複数の認証を行っている\
場合にこの不具合が発生します。認証をやりなおしてください。'''
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


def generate_message_from_events(events, reply_text):
    day_of_week_strs = ["月", "火", "水", "木", "金", "土", "日"]
    for e in events:
        summary = e['summary']
        start = e['start'].get('dateTime', e['start'].get('date'))
        if re.match('\d+[-]\d+[-]\d+[T]\d+[:]\d+[:]\d+[+]\d+[:]\d+', start):
            start_datetime = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S+09:00')
            day_of_week = day_of_week_strs[start_datetime.weekday()]
            start = start_datetime.strftime(
                '%Y年%m月%d日({}) %H時%S分'.format(day_of_week)
            )
            end = e['end'].get('dateTime', e['end'].get('date'))
            end_datetime = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S+09:00')
            day_of_week = day_of_week_strs[end_datetime.weekday()]
            end = end_datetime.strftime(
                '%Y年%m月%d日({}) %H時%S分'.format(day_of_week)
            )
            reply_text += '\n\n{}\n{}\n               |\n{}\n\n---------------------------'.format(summary,
                                                                                                   start,
                                                                                                   end)
        else:
            start_datetime = datetime.strptime(start, '%Y-%m-%d')
            start = start_datetime.strftime('%Y年%m月%d日')
            end = '終日'
            reply_text += '\n\n{}\n{} {}\n\n---------------------------'.format(summary,
                                                                                start,
                                                                                end)
    return reply_text

from .join_event_handler import JoinEventHandler
from .leave_event_handler import LeaveEventHandler
from .message_event_handler import MessageEventHandler
from .postback_event_handler import PostBackEventHandler
from .unfollow_event_handler import UnfollowEventHandler
