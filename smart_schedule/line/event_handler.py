# -*- coding: utf-8 -*-

from datetime import datetime
import flask
from flask import Flask
import urllib
import hashlib
from linebot import (
    LineBotApi
)
from linebot.exceptions import (
    LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage,
    PostbackEvent, StickerSendMessage)

from smart_schedule.line.module import (
    exit_confirm, post_carousel, get_join_contents_buttons
)
from smart_schedule.settings import line_env
from smart_schedule.settings import web_env
from smart_schedule.settings import hash_env
from smart_schedule.google_calendar import api_manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from smart_schedule.models import Personal
from smart_schedule.settings import db_env

app = Flask(__name__)

line_bot_api = LineBotApi(line_env['channel_access_token'])


def handle(handler, body, signature):
    handler.handle(body, signature)

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        print(event)
        if event.source.type == 'user':
            talk_id = event.source.user_id
        elif event.source.type == 'group':
            talk_id = event.source.group_id
        elif event.source.type == 'room':
            talk_id = event.source.room_id
        else:
            raise Exception('invalid `event.source`')
        # google calendar api のcredentialをDBから取得する
        credentials = api_manager.get_credentials(talk_id)
        # DBに登録されていない場合、認証URLをリプライする
        if credentials is None:
            google_auth_message(event)
            return
        service = api_manager.build_service(credentials)

        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # DBにアクセスし、セッションを開始
        engine = create_engine(db_env['database_url'])
        session = sessionmaker(bind=engine, autocommit=True)()
        with session.begin():
            person = session.query(Personal).filter(Personal.user_id == talk_id).one()
            if person.day_flag:
                person.day_flag = False
                days = int(event.message.text)
                events = api_manager.get_events_after_n_days(service, days)
                reply_text = '{}日後の予定'.format(days)
                for e in events:
                    summary = e['summary']
                    start = e['start'].get('dateTime', e['start'].get('date'))
                    start_datetime = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S+09:00')
                    start = start_datetime.strftime('%Y年%m月%d日 %H時%S分')
                    end = e['end'].get('dateTime', e['end'].get('date'))
                    end_datetime = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S+09:00')
                    end = end_datetime.strftime('%Y年%m月%d日 %H時%S分')
                    reply_text += '\n\n{}\n{}\n               |\n{}\n\n---------------------------'.format(summary,
                                                                                                           start,
                                                                                                           end)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return -1

            if person.up_to_day_flag:
                person.up_to_day_flag = False
                days = int(event.message.text)
                events = api_manager.get_n_days_events(service, days)
                reply_text = '{}日後までの予定'.format(days)
                for e in events:
                    summary = e['summary']
                    start = e['start'].get('dateTime', e['start'].get('date'))
                    start_datetime = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S+09:00')
                    start = start_datetime.strftime('%Y年%m月%d日 %H時%S分')
                    end = e['end'].get('dateTime', e['end'].get('date'))
                    end_datetime = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S+09:00')
                    end = end_datetime.strftime('%Y年%m月%d日 %H時%S分')
                    reply_text += '\n\n{}\n{}\n               |\n{}\n\n---------------------------'.format(summary,
                                                                                                           start,
                                                                                                           end)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return -1

            if person.keyword_flag:
                person.keyword_flag = False
                keyword = event.message.text
                events = api_manager.get_events_by_title(service, keyword)
                reply_text = '{}の検索結果'.format(keyword)
                for e in events:
                    summary = e['summary']
                    start = e['start'].get('dateTime', e['start'].get('date'))
                    start_datetime = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S+09:00')
                    start = start_datetime.strftime('%Y年%m月%d日 %H時%S分')
                    end = e['end'].get('dateTime', e['end'].get('date'))
                    end_datetime = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S+09:00')
                    end = end_datetime.strftime('%Y年%m月%d日 %H時%S分')
                    reply_text += '\n\n{}\n{}\n               |\n{}\n\n---------------------------'.format(summary,
                                                                                                           start,
                                                                                                           end)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return -1

        if event.message.text == "#menu":
            post_carousel(event.reply_token)
            return -1
        if not event.message.text.startswith("予定 "):
            if event.message.text.startswith("大好き"):
                reply_text = "大好きだよ！！！".format(event.message.text)
            elif event.message.text.startswith("退出") and not event.source.type == "user":
                confirm_message = TemplateSendMessage(
                    alt_text='Confirm template',
                    template=exit_confirm(time)
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    confirm_message
                )
                return -1
            else:
                reply_text = event.message.text

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            return -1

        schedule_name = event.message.text.split(maxsplit=1)[1]
        buttons_template_message = TemplateSendMessage(
            alt_text='Buttons template',
            template=get_join_contents_buttons(schedule_name, time)
        )
        print(buttons_template_message)
        # text_send_message = TextSendMessage(text=reply_text)
        line_bot_api.reply_message(
            event.reply_token,
            buttons_template_message
        )

    @handler.add(PostbackEvent)
    def handle_postback(event):
        print("postbackevent: {}".format(event))
        if event.source.type == 'user':
            talk_id = event.source.user_id
        elif event.source.type == 'group':
            talk_id = event.source.group_id
        elif event.source.type == 'room':
            talk_id = event.source.room_id
        else:
            raise Exception('invalid `event.source`')
        data = event.postback.data.split(',')
        print(data)
        print(data[1])
        pre_time = datetime.strptime(data[1],'%Y-%m-%d %H:%M:%S')
        compare = datetime.now()-pre_time
        print(compare)
        if compare.total_seconds() < 20:
            if data[0] == "yes" and event.source.type == "group":
                try:
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id="2", sticker_id="42")
                    )
                    line_bot_api.leave_group(event.source.group_id)
                except LineBotApiError as e:
                    print(e)
            elif data[0] == "yes" and event.source.type == "room":
                print("OK")
                try:
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id="2", sticker_id="42")
                    )
                    line_bot_api.leave_room(event.source.room_id)
                except LineBotApiError as e:
                    print(e)
            elif data[0] == "no":
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="退出をキャンセルします。")
                )
            else:
                # DBにアクセスし、セッションを開始
                engine = create_engine(db_env['database_url'])
                session = sessionmaker(bind=engine, autocommit=True)()
                with session.begin():
                    person = session.query(Personal).filter(Personal.user_id == talk_id).one()
                    if data[0] == "#keyword_search":
                        person.keyword_flag = True
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="キーワードを入力してください\n例：バイト、研究室")
                        )
                    elif data[0] == "#after n days_schedule":
                        person.day_flag = True
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="何日後の予定を表示しますか？\n例：5")
                        )
                    elif data[0] == "#up to n days_schedule":
                        person.up_to_day_flag = True
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="何日後までの予定を表示しますか？\n例：5")
                        )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="タイムアウトです。\nもう一度最初からやり直してください")
            )


def google_auth_message(event):
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

