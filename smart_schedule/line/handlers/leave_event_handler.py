from linebot.models import LeaveEvent
from smart_schedule.google_calendar import api_manager
from smart_schedule.settings import REFRESH_ERROR


class LeaveEventHandler:
    def __init__(self, handler):
        self.handler = handler

        @self.handler.add(LeaveEvent)
        def handle(event):
            print(event)
            talk_id = event.source.group_id
            credentials = api_manager.get_credentials(talk_id)
            if credentials == REFRESH_ERROR:
                print('リフレッシュエラーが起きたのでremove_accountを行いません')
                return
            elif credentials is not None:
                api_manager.remove_account(credentials, talk_id)

