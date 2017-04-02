# -*- coding: utf-8 -*-
from oauth2client import client
from datetime import datetime, date
from collections import OrderedDict, Counter
import flask
import urllib
import hashlib
import re
from linebot import (
    LineBotApi
)
from linebot.exceptions import (
    LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage,
    PostbackEvent, StickerSendMessage, JoinEvent, LeaveEvent, UnfollowEvent)

from smart_schedule.line.module import post_carousel
from smart_schedule.domain.line_templates import (
    AccountRemoveConfirm, EventCreateButtons, ExitConfirm, GroupMenuButtons
)
from smart_schedule.settings import (
    line_env, web_env, hash_env, messages, Session, REFRESH_ERROR
)
from smart_schedule.google_calendar import api_manager
from smart_schedule.models import Personal, GroupUser, FreeDay

line_bot_api = LineBotApi(line_env['channel_access_token'])


def handle(handler, body, signature):
    handler.handle(body, signature)

    @handler.add(JoinEvent)
    def handle_join(event):
        print(event)
        join_message = '''グループに招待ありがとうございます！
グループでは「予定調整機能」「グループに登録されたカレンダーの予定確認」ができます。
詳しい使い方はアカウント紹介ページを見てください。
グループで使用できるコマンドを呼び出すメッセージは「help」と送信すると見ることができます。'''
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=join_message)
        )

    @handler.add(LeaveEvent)
    def handle_leave(event):
        print(event)
        talk_id = event.source.group_id
        credentials = api_manager.get_credentials(talk_id)
        if credentials == REFRESH_ERROR:
            print('リフレッシュエラーが起きたのでremove_accountを行いません')
            return
        elif credentials is not None:
            api_manager.remove_account(credentials, talk_id)

    @handler.add(UnfollowEvent)
    def handle_unfollow(event):
        print(event)
        talk_id = event.source.user_id
        credentials = api_manager.get_credentials(talk_id)
        if credentials == REFRESH_ERROR:
            print('リフレッシュエラーが起きたのでremove_accountを行いません')
            return
        elif credentials is not None:
            api_manager.remove_account(credentials, talk_id)

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        print(event)
        session = Session()
        if event.source.type == 'user':
            talk_id = event.source.user_id
        elif event.source.type == 'group':
            talk_id = event.source.group_id
        elif event.source.type == 'room':
            talk_id = event.source.room_id
        else:
            raise Exception('invalid `event.source`')

        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 退出の確認を表示
        if event.message.text == "exit" and not event.source.type == "user":
            confirm_message = TemplateSendMessage(
                alt_text='Confirm template',
                template=ExitConfirm(time, messages['templates']['exit_confirm'])
            )
            line_bot_api.reply_message(
                event.reply_token,
                confirm_message
            )
            return -1

        if event.message.text == 'help':
            if event.source.type == 'user':
                reply_text = '''コマンド一覧

help: ヘルプを表示
select: カレンダー選択
logout: Google アカウントとの連携を解除

詳しい使い方はアカウント紹介ページを見てください'''
            else:
                reply_text = '''コマンド一覧

help: ヘルプを表示
ss: グループメニューの表示
select: カレンダー選択
logout: Google アカウントとの連携を解除
exit: Smart Schedule を退会させる(アカウント連携も自動的に削除されます)

詳しい使い方はアカウント紹介ページを見てください'''
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            return -1

        # google calendar api のcredentialをDBから取得する
        credentials = api_manager.get_credentials(talk_id)
        # リフレッシュエラーが起きた場合、手動でアカウント連携を解除するように促すメッセージを送る
        if credentials == REFRESH_ERROR:
            reply_refresh_error_message(event)
            return
        # DBに登録されていない場合、認証URLをリプライする
        if credentials is None:
            reply_google_auth_message(event)
            return
        service = api_manager.build_service(credentials)

        # メニューを表示する
        if event.message.text == "#menu":
            post_carousel(event.reply_token)
            return -1

        # グループのメニューを表示する
        pattern = r'(ss|smart[\s_-]?schedule|スマートスケジュール)$'
        if re.match(pattern, event.message.text, re.IGNORECASE) and not event.source.type == "user":
            buttons_template_message = TemplateSendMessage(
                alt_text='Button template',
                template=GroupMenuButtons(
                    time,
                    messages['templates']['group_menu_buttons']
                )
            )
            line_bot_api.reply_message(
                event.reply_token,
                buttons_template_message
            )
            return -1

        with session.begin():
            person = session.query(Personal).filter(Personal.user_id == talk_id).one()
            if person.day_flag:
                person.day_flag = False
                days = int(event.message.text)
                try:
                    events = api_manager.get_events_after_n_days(service,  person.calendar_id, days)
                except client.HttpAccessTokenRefreshError:
                    session.delete(person)
                    reply_invalid_credential_error_message(event)
                    return
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
                try:
                    events = api_manager.get_n_days_events(service,  person.calendar_id, days)
                except client.HttpAccessTokenRefreshError:
                    session.delete(person)
                    reply_invalid_credential_error_message(event)
                    return
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
                try:
                    events = api_manager.get_events_by_title(service, person.calendar_id, keyword)
                except client.HttpAccessTokenRefreshError:
                    session.delete(person)
                    reply_invalid_credential_error_message(event)
                    return
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
                session.add(GroupUser(name=username, group_id=person.id))
                reply_text = '{}をグループのメンバーに登録しました'.format(username)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return -1

            if event.message.text == 'select':
                try:
                    calendar_list = api_manager.get_calendar_list(service)
                except client.HttpAccessTokenRefreshError:
                    session.delete(person)
                    reply_invalid_credential_error_message(event)
                    return
                reply_text = 'Google Calendar で確認できるカレンダーの一覧です。\n 文字を入力してカレンダーを選択してください'
                for item in calendar_list['items']:
                    reply_text += '\n- {}'.format(item['summary'])
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                person.calendar_select_flag = True
                return -1

            if person.calendar_select_flag:
                try:
                    calendar_list = api_manager.get_calendar_list(service)
                except client.HttpAccessTokenRefreshError:
                    session.delete(person)
                    reply_invalid_credential_error_message(event)
                    return
                summaries = [item['summary'] for item in calendar_list['items']]
                if event.message.text in summaries:
                    person.calendar_select_flag = False
                    calendar_id = [item['id'] for item in calendar_list['items'] if item['summary'] == event.message.text][0]
                    person.calendar_id = calendar_id
                    reply_text = 'カレンダーを {} に設定しました'.format(event.message.text)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply_text)
                    )
                else:
                    person.calendar_select_flag = False
                    reply_text = '{} はカレンダーには存在しません'.format(event.message.text)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply_text)
                    )

            if event.message.text == 'logout':
                confirm_message = TemplateSendMessage(
                    alt_text='Confirm template',
                    template=AccountRemoveConfirm(
                        time,
                        messages['templates']['account_remove_confirm']
                    )
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    confirm_message
                )

            if person.adjust_flag:
                group_users = session.query(GroupUser).filter(GroupUser.group_id == person.id).all()
                # グループのメンバーをシステムに登録していなかった場合
                if len(group_users) == 0:
                    reply_text = 'グループのメンバーを登録してください\n例：メンバー登録 橋本'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply_text)
                    )
                    person.adjust_flag = False
                    return -1

                # グループの予定調整を終了
                if event.message.text == "end":
                    reply_text = '空いている日'
                    dates = []
                    for group_user in group_users:
                        dates.extend([free_day.date for free_day in group_user.free_days])
                        for free_day in group_user.free_days:
                            session.delete(free_day)

                    date_count_dict = OrderedDict(sorted(Counter(dates).items(), key=lambda x: x[0]))
                    for i, dic in enumerate(date_count_dict.items()):
                        d, count = dic
                        if i % 3 == 0:
                            reply_text += '\n'
                        else:
                            reply_text += ', '
                        reply_text += '{}/{} {}人'.format(d.month, d.day, count)

                    best_date_count = max(date_count_dict.values())
                    best_dates = [k for k, v in date_count_dict.items() if v == best_date_count]
                    print(len(reply_text))
                    buttons_template_message = TemplateSendMessage(
                        alt_text='Button template',
                        # TODO ボタンテンプレートが4つしか受け付けないので4つしか選べない
                        template=EventCreateButtons(
                            time,
                            messages['templates']['event_create_buttons'],
                            reply_text,
                            best_dates[:4]
                        )
                    )
                    line_bot_api.reply_message(
                        event.reply_token,
                        buttons_template_message
                    )
                    person.adjust_flag = False
                    return -1

                user_names = tuple(group_user.name for group_user in group_users)
                if event.message.text.startswith(user_names):
                    split_message = event.message.text.split()
                    name = split_message[0]
                    group_user = [group_user for group_user in group_users if group_user.name == name][0]
                    day_strs = split_message[1:]
                    datetimes = [datetime.strptime(day_str, '%m/%d') for day_str in day_strs]
                    # TODO 2017 にしちゃってるけどどうにかしないと1年後使えねえや笑
                    dates = [date(2017, datetime.month, datetime.day) for datetime in datetimes]
                    free_days = [FreeDay(date, group_user.id) for date in dates]
                    session.add_all(free_days)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='空いている日を保存しました')
                    )
                    return -1

    @handler.add(PostbackEvent)
    def handle_postback(event):
        print("postbackevent: {}".format(event))
        session = Session()
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
        pre_time = datetime.strptime(data[-1], '%Y-%m-%d %H:%M:%S')
        compare = datetime.now()-pre_time
        print(compare)

        if compare.total_seconds() < int(line_env['time_out_seconds']):
            credentials = api_manager.get_credentials(talk_id)
            if credentials == REFRESH_ERROR:
                reply_refresh_error_message(event)
                return

            if data[0] == "ExitConfirm_yes" and event.source.type == "group":
                try:
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id="2", sticker_id="42")
                    )
                    if credentials is not None:
                        api_manager.remove_account(credentials, talk_id)
                    line_bot_api.leave_group(event.source.group_id)
                    return
                except LineBotApiError as e:
                    print(e)
            elif data[0] == "ExitConfirm_yes" and event.source.type == "room":
                print("OK")
                try:
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id="2", sticker_id="42")
                    )
                    if credentials is not None:
                        api_manager.remove_account(credentials, talk_id)
                    line_bot_api.leave_room(event.source.room_id)
                    return
                except LineBotApiError as e:
                    print(e)

            if credentials is None:
                reply_google_auth_message(event)
                return
            service = api_manager.build_service(credentials)

            if data[0] == "ExitConfirm_no":
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="退出をキャンセルしました。")
                )
            elif data[0] == "AccountRemoveConfirm_yes":
                api_manager.remove_account(credentials, talk_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='アカウント連携を解除しました。')
                )
            elif data[0] == "AccountRemoveConfirm_no":
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="アカウント連携解除をキャンセルしました。")
                )
            elif data[0] == "GroupMenuButtons_#g-calender":
                post_carousel(event.reply_token)
            elif data[0] == "GroupMenuButtons_#register":
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='メンバー登録の仕方\n例：メンバー登録 橋本')
                )
            elif data[0] == "EventCreateButtons_#create-calendar":
                created_datetime = datetime.strptime(data[1], '%m/%d')
                # TODO 2017
                created_date = date(2017, created_datetime.month, created_datetime.day)
                title = 'Smart Scheduleからの予定'
                with session.begin():
                    person = session.query(Personal).filter(Personal.user_id == talk_id).one()
                try:
                    calendar_event = api_manager.create_event(service, person.calendar_id, created_date, title)
                except client.HttpAccessTokenRefreshError:
                    session.delete(person)
                    reply_invalid_credential_error_message(event)
                    return
                reply_text = '{}月{}日の予定を作成しました\n{}'.format(
                    created_date.month, created_date.day, calendar_event.get('htmlLink')
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
            else:
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
                    elif data[0] == "#today_schedule":
                        days = 0
                        try:
                            events = api_manager.get_events_after_n_days(service, person.calendar_id, days)
                        except client.HttpAccessTokenRefreshError:
                            session.delete(person)
                            reply_invalid_credential_error_message(event)
                            return
                        reply_text = '今日の予定'
                        reply_text = generate_message_from_events(events, reply_text)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                    elif data[0] == "#tomorrow_schedule":
                        days = 1
                        try:
                            events = api_manager.get_events_after_n_days(service, person.calendar_id, days)
                        except client.HttpAccessTokenRefreshError:
                            session.delete(person)
                            reply_invalid_credential_error_message(event)
                            return
                        reply_text = '明日の予定'
                        reply_text = generate_message_from_events(events, reply_text)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                    elif data[0] == "#7days_schedule":
                        days = 7
                        try:
                            events = api_manager.get_n_days_events(service, person.calendar_id, days)
                        except client.HttpAccessTokenRefreshError:
                            session.delete(person)
                            reply_invalid_credential_error_message(event)
                            return
                        reply_text = '1週間後までの予定'
                        reply_text = generate_message_from_events(events, reply_text)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                    # グループメンバー一覧を表示
                    elif data[0] == "GroupMenuButtons_#member":
                        members = session.query(GroupUser).filter(GroupUser.group_id == person.id).all()
                        print(members)
                        reply_text = '登録されているメンバー一覧\n'
                        for e in members:
                            reply_text += e.name
                            reply_text += '\n'
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                    # 調整機能の呼び出し
                    elif data[0] == "GroupMenuButtons_#adjust":
                        members = session.query(GroupUser).filter(GroupUser.group_id == person.id).all()
                        # グループのメンバーをシステムに登録していなかった場合
                        if len(members) == 0:
                            reply_text = 'グループのメンバーを登録してください\n例：メンバー登録 橋本'
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=reply_text)
                            )
                            return -1
                        person.adjust_flag = True
                        reply_text = "空いてる日を入力してください\n例：橋本 1/1 1/2 1/3 1/4\n\n※予定調整を終了する際は「end」と入力してください\n--------------------------------"
                        for member in members:
                            if len(member.free_days) != 0:
                                break
                        else:
                            reply_text += '\n\n現在、空いている日は登録されていません'
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=reply_text)
                            )
                            return -1

                        reply_text += '\n\n現在の空いている日\n'
                        dates = []
                        for member in members:
                            dates.extend([free_day.date for free_day in member.free_days])
                        date_count_dict = OrderedDict(sorted(Counter(dates).items(), key=lambda x: x[0]))
                        for d, count in date_count_dict.items():
                            reply_text += '\n{}/{} {}票'.format(d.month, d.day, count)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )

        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="タイムアウトです。\nもう一度最初からやり直してください")
            )


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
    reply_text = '''認証情報の更新エラーが発生しました。同じGoogleアカウントで複数の認証を行っている場合にこの不具合が発生します。このトークでSmart Scheduleを使用したい場合は以下のいずれかを行った後で認証しなおしてください。

1. 同じアカウントで認証しているトークでlogoutコマンドを行う(オススメ)

2. 下記URLから手動でSmart Scheduleの認証を解除する https://myaccount.google.com/u/1/permissions'''
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


def reply_invalid_credential_error_message(event):
    reply_text = '無効な認証情報です。同じGoogleアカウントで複数の認証を行っている場合にこの不具合が発生します。認証をやりなおしてください。'
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


def generate_message_from_events(events, reply_text):
    for e in events:
        summary = e['summary']
        start = e['start'].get('dateTime', e['start'].get('date'))
        if re.match('\d+[-]\d+[-]\d+[T]\d+[:]\d+[:]\d+[+]\d+[:]\d+', start):
            start_datetime = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S+09:00')
            start = start_datetime.strftime('%Y年%m月%d日 %H時%S分')
            end = e['end'].get('dateTime', e['end'].get('date'))
            end_datetime = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S+09:00')
            end = end_datetime.strftime('%Y年%m月%d日 %H時%S分')
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
