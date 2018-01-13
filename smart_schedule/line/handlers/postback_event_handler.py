from datetime import datetime, date
from collections import OrderedDict, Counter
from oauth2client import client
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
from smart_schedule.models import Talk
from smart_schedule.utils.date_util import jst, is_over_now

from . import (
    line_bot_api, reply_google_auth_message, reply_refresh_error_message,
    reply_invalid_credential_error_message, generate_message_from_events
)


class PostBackEventHandler:
    def __init__(self, handler):
        self.handler = handler
        self.cases = []
        self.preexe_cases = []
        self.session = Session()

        @self._add_case(template_id='ExitConfirm_yes', preexe=True)
        def exit_confirm(event, data, credentials):
            try:
                talk_id = self._get_talk_id(event)
                line_bot_api.reply_message(
                    event.reply_token,
                    StickerSendMessage(package_id="2", sticker_id="42")
                )
                if credentials is not None:
                    api_manager.remove_account(credentials, talk_id)
                if event.source.type == 'group':
                    line_bot_api.leave_group(event.source.group_id)
                else:
                    line_bot_api.leave_room(event.source.room_id)
            except LineBotApiError as e:
                print(e)

        @self._add_case(template_id='ExitConfirm_no', preexe=True)
        def exit_confirm_no(event, data, credentials):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="退出をキャンセルしました。")
            )

        @self._add_case(template_id='AccountRemoveConfirm_yes')
        def account_remove(event, data, credentials, _):
            talk_id = self._get_talk_id(event)
            api_manager.remove_account(credentials, talk_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='アカウント連携を解除しました。')
            )

        @self._add_case(template_id='AccountRemoveConfirm_no')
        def account_remove_no(event, data, credentials, service):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="アカウント連携解除をキャンセルしました。")
            )

        @self._add_case(template_id='EventCreateButtons_#create-calendar')
        def calendar_create(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            created_datetime = datetime.strptime(data[1], '%m/%d')
            current_year = datetime.now(jst).year
            created_date = date(
                current_year if is_over_now(created_datetime)
                else current_year + 1,
                created_datetime.month, created_datetime.day
            )
            title = 'Smart Scheduleからの予定'
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
            try:
                calendar_event = api_manager.create_event(
                    service, talk.calendar_id, created_date, title
                )
            except client.HttpAccessTokenRefreshError:
                with self.session.begin():
                    self.session.delete(talk)
                reply_invalid_credential_error_message(event)
                return
            reply_text = '{}月{}日の予定を作成しました\n{}'.format(
                created_date.month, created_date.day, calendar_event.get('htmlLink')
            )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        @self._add_case(template_id='GroupMenuButtons_#member')
        def member_display(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            reply_text = '登録されているメンバー一覧'
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
            user_names = sorted({free_day.user_name for free_day in talk.free_days})
            for user_name in user_names:
                reply_text += '\n'
                reply_text += user_name
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        @self._add_case(template_id='GroupMenuButtons_#adjust')
        def schedule_adjust(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()

            reply_text = "空いてる日を入力してください\n例：橋本 1/1 1/2 1/3 1/4\n\n※日程調整を終了する際は「end」と入力してください\n--------------------------------"
            if len(talk.free_days) == 0:
                reply_text += '\n\n現在、空いている日は登録されていません'
            else:
                reply_text += '\n\n現在の空いている日\n'
                dates = [free_day.date for free_day in talk.free_days]
                date_count_dict = OrderedDict(sorted(Counter(dates).items(), key=lambda x: x[0]))
                for d, count in date_count_dict.items():
                    reply_text += '\n{}/{} {}票'.format(d.month, d.day, count)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        @self._add_case(template_id='GroupMenuButtons_#g-calender')
        def schedule_display(event, data, credentials, service):
            post_carousel(event.reply_token)

        @self._add_case(template_id='#keyword_search')
        def keyword_search(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
                talk.keyword_flag = True
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="キーワードを入力してください\n例：バイト、研究室")
            )

        @self._add_case(template_id='#up to n days_schedule')
        def up_to_n_days_schedule(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
                talk.up_to_day_flag = True
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="何日後までの予定を表示しますか？\n例：5")
            )

        @self._add_case(template_id='#date_schedule')
        def date_schedule(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
                talk.date_flag = True
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="取得したい予定の日付を入力してください\n例：4/1")
            )

        @self._add_case(template_id='#today_schedule')
        def today_schedule(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
            days = 0
            try:
                events = api_manager.get_events_after_n_days(service, talk.calendar_id, days)
            except client.HttpAccessTokenRefreshError:
                with self.session.begin():
                    self.session.delete(talk)
                reply_invalid_credential_error_message(event)
                return
            reply_text = '今日の予定'
            reply_text = generate_message_from_events(events, reply_text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        @self._add_case(template_id='#tomorrow_schedule')
        def tomorrow_schedule(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
            days = 1
            try:
                events = api_manager.get_events_after_n_days(service, talk.calendar_id, days)
            except client.HttpAccessTokenRefreshError:
                with self.session.begin():
                    self.session.delete(talk)
                reply_invalid_credential_error_message(event)
                return
            reply_text = '明日の予定'
            reply_text = generate_message_from_events(events, reply_text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        @self._add_case(template_id='#7days_schedule')
        def seven_days_schedule(event, data, credentials, service):
            talk_id = self._get_talk_id(event)
            with self.session.begin():
                talk = self.session.query(Talk).filter_by(talk_id=talk_id).one()
            days = 7
            try:
                events = api_manager.get_n_days_events(service, talk.calendar_id, days)
            except client.HttpAccessTokenRefreshError:
                with self.session.begin():
                    self.session.delete(talk)
                reply_invalid_credential_error_message(event)
                return
            reply_text = '1週間後までの予定'
            reply_text = generate_message_from_events(events, reply_text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        @self.handler.add(PostbackEvent)
        def handle(event):
            print("postbackevent: {}".format(event))
            session = Session()
            data = event.postback.data.split(',')
            print(data)
            print(data[1])
            pre_time = datetime.strptime(data[-1], '%Y-%m-%d %H:%M:%S')
            compare = datetime.now() - pre_time
            print(compare)

            if compare.total_seconds() > int(line_env['time_out_seconds']):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="タイムアウトです。\nもう一度最初からやり直してください")
                )
                return

            talk_id = self._get_talk_id(event)
            credentials = api_manager.get_credentials(talk_id)
            if credentials == REFRESH_ERROR:
                reply_refresh_error_message(event)
                return

            for func, template_id in self.preexe_cases:
                if data[0] == template_id:
                    func(event, data, credentials)
                    return

            service = api_manager.build_service(credentials)
            if service is None:
                reply_google_auth_message(event)
                return

            for func, template_id in self.cases:
                if data[0] == template_id:
                    func(event, data, credentials, service)
                    return

    def _add_case(self, template_id=None, preexe=False):
        """A decorator that is used to register a function executing 
        in case of matching given filtering rules.

        :param template_id: the template data rule as string.
        :param preexe: the boolean indicating whether function is pre-executed.
        """
        def wrapper(func):
            if preexe:
                self.preexe_cases.append((func, template_id))
            else:
                self.cases.append((func, template_id))
            return func

        return wrapper

    @staticmethod
    def _get_talk_id(event):
        if event.source.type == 'user':
            talk_id = event.source.user_id
        elif event.source.type == 'group':
            talk_id = event.source.group_id
        elif event.source.type == 'room':
            talk_id = event.source.room_id
        else:
            raise Exception('invalid `event.source`')
        return talk_id

    @classmethod
    def _get_service(cls, event):
        talk_id = cls._get_talk_id(event)
        # google calendar api のcredentialをDBから取得する
        credentials = api_manager.get_credentials(talk_id)
        if credentials == REFRESH_ERROR or credentials is None:
            return credentials
        service = api_manager.build_service(credentials)
        return service
