from oauth2client import client
from datetime import datetime, date
from collections import OrderedDict, Counter
import re
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage
)

from smart_schedule.line.module import post_carousel
from smart_schedule.domain.line_templates import (
    AccountRemoveConfirm, EventCreateButtons, ExitConfirm, GroupMenuButtons
)
from smart_schedule.settings import (
    messages, Session, REFRESH_ERROR
)
from smart_schedule.google_calendar import api_manager
from smart_schedule.models import Personal, GroupUser, FreeDay

from . import (
    line_bot_api, reply_google_auth_message, reply_refresh_error_message,
    reply_invalid_credential_error_message, generate_message_from_events
)


class MessageEventHandler:
    def __init__(self, handler):
        self.handler = handler

        @self.handler.add(MessageEvent, message=TextMessage)
        def handle(event):
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

