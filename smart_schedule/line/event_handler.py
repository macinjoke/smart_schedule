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
from smart_schedule.models import Personal, GroupUser, FreeDay
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

        # メニューを表示する
        if event.message.text == "#menu":
            post_carousel(event.reply_token)
            return -1

        # グループのメニューを表示する
        if event.message.text == "Gmenu" and not event.source.type == "user":
            buttons_template_message = get_join_contents_buttons(time=time)
            line_bot_api.reply_message(
                event.reply_token,
                buttons_template_message
            )
            return -1

        # 退出の確認を表示
        if event.message.text == "退出" and not event.source.type == "user":
            confirm_message = TemplateSendMessage(
                alt_text='Confirm template',
                template = exit_confirm(time)
            )
            line_bot_api.reply_message(
                event.reply_token,
                confirm_message
            )
            return -1

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
                reply_text = generate_message_from_events(events, reply_text)
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
                reply_text = generate_message_from_events(events, reply_text)
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
                reply_text = generate_message_from_events(events, reply_text)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return -1
            # グループでのメンバー登録
            if event.message.text.startswith("メンバー登録 ") and not event.source.type == 'user':
                username = event.message.text.split(maxsplit=1)[1]
                session.add(GroupUser(name=username, group_id=talk_id))
                reply_text = '{}をグループのメンバーに登録しました'.format(username)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return -1

            if person.adjust_flag:
                # グループの予定調整を終了
                if event.message.text == "OK!!":
                    person.adjust_flag = False
                    return -1
                group_member = session.query(GroupUser).filter(GroupUser.group_id == talk_id)
                # グループのメンバーをシステムに登録していなかった場合
                if len(group_member) == 0:
                    reply_text = 'グループのメンバーを登録してください\n例：メンバー登録 橋本'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply_text)
                    )
                    return -1
                data = event.message.text.split(' ')
                if len(data) <= 1:
                    return -1
                name = data[0]
                days = data[1]
                date = days.split(',')

        # schedule_name = event.message.text.split(maxsplit=1)[1]
        # buttons_template_message = TemplateSendMessage(
        #     alt_text='Buttons template',
        #     template=get_join_contents_buttons(schedule_name, time)
        # )
        # print(buttons_template_message)
        # # text_send_message = TextSendMessage(text=reply_text)
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     buttons_template_message
        # )

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
            elif data[0] == "#g-calender":
                post_carousel(event.reply_token)
            elif data[0] == "#register":
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='メンバー登録の仕方\n例：メンバー登録 橋本')
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
                    elif data[0] == "#today_schedeule":
                        credentials = api_manager.get_credentials(line_env['user_id'])
                        service = api_manager.build_service(credentials)
                        days = 0
                        events = api_manager.get_events_after_n_days(service, days)
                        reply_text = '今日の予定'
                        reply_text = generate_message_from_events(events, reply_text)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                    elif data[0] == "#tomorrow_schedule":
                        credentials = api_manager.get_credentials(line_env['user_id'])
                        service = api_manager.build_service(credentials)
                        days = 1
                        events = api_manager.get_events_after_n_days(service, days)
                        reply_text = '明日の予定'
                        reply_text = generate_message_from_events(events, reply_text)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                    elif data[0] == "#7days_schedule":
                        credentials = api_manager.get_credentials(line_env['user_id'])
                        service = api_manager.build_service(credentials)
                        days = 7
                        events = api_manager.get_events_after_n_days(service, days)
                        reply_text = '明日の予定'
                        reply_text = generate_message_from_events(events, reply_text)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                    # グループメンバー一覧を表示
                    elif data[0] == "#member":
                        member = session.query(GroupUser).filter(GroupUser.group_id == talk_id)
                        reply_text = '登録されているメンバー一覧\n'
                        for e in member:
                            reply_text += e + '\n'
                    # 調整機能の呼び出し
                    elif data[0] == "#adjust":
                        person.adjust_flag = True
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="空いてる日を入力してください\n例：橋本 1/1,1/2,1/3,1/4\n予定調整を終了する際は「OK!!」と入力してください")
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


def generate_message_from_events(events, reply_text):
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
    return reply_text
