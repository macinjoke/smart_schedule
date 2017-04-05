from linebot import (
    LineBotApi, WebhookHandler
)
from smart_schedule.settings import line_env

from .handlers import (
    JoinEventHandler, LeaveEventHandler, MessageEventHandler,
    PostBackEventHandler, UnfollowEventHandler
)

line_bot_api = LineBotApi(line_env['channel_access_token'])


class EventHandler:

    def __init__(self):
        handler = WebhookHandler(line_env['channel_secret'])
        self._load_handler(handler)
        self.handler = handler

    @staticmethod
    def _load_handler(handler):
        # TODO 動的ロードに出来ないか検討
        JoinEventHandler(handler)
        LeaveEventHandler(handler)
        MessageEventHandler(handler)
        PostBackEventHandler(handler)
        UnfollowEventHandler(handler)
        return handler
