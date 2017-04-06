from linebot.models import JoinEvent, TextSendMessage
from smart_schedule.settings import messages
from . import line_bot_api


class JoinEventHandler:
    join_event_messages = messages['text_messages']['join_event']

    def __init__(self, handler):
        self.handler = handler

        @self.handler.add(JoinEvent)
        def handle(event):
            print(event)
            message = self.join_event_messages['join_message']
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )
