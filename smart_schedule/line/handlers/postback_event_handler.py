from oauth2client import client
from datetime import datetime, date
from collections import OrderedDict, Counter
from linebot.exceptions import (
    LineBotApiError
)
from linebot.models import (
    TextSendMessage,
    PostbackEvent, StickerSendMessage)

from smart_schedule.line.module import post_carousel
from smart_schedule.settings import (
    line_env, Session, REFRESH_ERROR
)
from smart_schedule.google_calendar import api_manager
from smart_schedule.models import Talk, FreeDay

from . import (
    line_bot_api, reply_google_auth_message, reply_refresh_error_message,
    reply_invalid_credential_error_message, generate_message_from_events
)


class PostBackEventHandler:
    def __init__(self, handler):
        self.handler = handler

        @self.handler.add(PostbackEvent)
        def handle(event):
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
                elif data[0] == "EventCreateButtons_#create-calendar":
                    created_datetime = datetime.strptime(data[1], '%m/%d')
                    # TODO 2017
                    created_date = date(2017, created_datetime.month, created_datetime.day)
                    title = 'Smart Scheduleからの予定'
                    with session.begin():
                        talk = session.query(Talk).filter(Talk.talk_id == talk_id).one()
                    try:
                        calendar_event = api_manager.create_event(service, talk.calendar_id, created_date, title)
                    except client.HttpAccessTokenRefreshError:
                        session.delete(talk)
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
                        talk = session.query(Talk).filter(Talk.talk_id == talk_id).one()
                        if data[0] == "#keyword_search":
                            talk.keyword_flag = True
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="キーワードを入力してください\n例：バイト、研究室")
                            )
                        elif data[0] == "#after n days_schedule":
                            talk.day_flag = True
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="何日後の予定を表示しますか？\n例：5")
                            )
                        elif data[0] == "#up to n days_schedule":
                            talk.up_to_day_flag = True
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="何日後までの予定を表示しますか？\n例：5")
                            )
                        elif data[0] == "#today_schedule":
                            days = 0
                            try:
                                events = api_manager.get_events_after_n_days(service, talk.calendar_id, days)
                            except client.HttpAccessTokenRefreshError:
                                session.delete(talk)
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
                                events = api_manager.get_events_after_n_days(service, talk.calendar_id, days)
                            except client.HttpAccessTokenRefreshError:
                                session.delete(talk)
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
                                events = api_manager.get_n_days_events(service, talk.calendar_id, days)
                            except client.HttpAccessTokenRefreshError:
                                session.delete(talk)
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
                            reply_text = '登録されているメンバー一覧'
                            free_days = session.query(FreeDay).filter_by(talk_id=talk.id).all()
                            user_names = sorted({free_day.user_name for free_day in free_days})
                            for user_name in user_names:
                                reply_text += '\n'
                                reply_text += user_name
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=reply_text)
                            )

                        # 調整機能の呼び出し
                        elif data[0] == "GroupMenuButtons_#adjust":
                            reply_text = "空いてる日を入力してください\n例：橋本 1/1 1/2 1/3 1/4\n\n※日程調整を終了する際は「end」と入力してください\n--------------------------------"
                            free_days = session.query(FreeDay).filter_by(talk_id=talk.id).all()
                            if len(free_days) == 0:
                                reply_text += '\n\n現在、空いている日は登録されていません'
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(text=reply_text)
                                )
                                return

                            reply_text += '\n\n現在の空いている日\n'
                            dates = [free_day.date for free_day in free_days]
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

