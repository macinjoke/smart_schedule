from linebot import LineBotApi

from linebot.models import (
    MessageEvent, TextMessage, TemplateSendMessage,
    PostbackTemplateAction, MessageTemplateAction, URITemplateAction, ButtonsTemplate,
    PostbackEvent
)

import datetime

from smart_schedule.settings import line_env
from smart_schedule.google_calendar import api_manager

line_bot_api = LineBotApi(line_env['channel_access_token'])


def handle(handler, body, signature):
    handler.handle(body, signature)

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        print(event)
        if not event.message.text.startswith("予定 "):
            return -1

        schedule_name = event.message.text.split(maxsplit=1)[1]
        buttons_template_message = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                # 芝刈り機のイラスト
                thumbnail_image_url='https://2.bp.blogspot.com/-SObo8z0Ajyw/V9ppuyMxT2I/AAAAAAAA9xI/jwNeixWhDeMJ6K_z96edB45umM6WTftVQCLcB/s800/kusakari_shibakari.png',
                title="{} の予定".format(schedule_name),
                text="選択してね",
                actions=[
                    PostbackTemplateAction(
                        label='参加する',
                        data='join'
                    ),
                    PostbackTemplateAction(
                        label='参加しない',
                        data='nojoin'
                    ),
                    MessageTemplateAction(
                        label='うっひょおお！！！',
                        text='うっひょおお！！！'
                    ),
                    URITemplateAction(
                        label='uri',
                        uri='http://example.com/'
                    )
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            buttons_template_message
        )

    @handler.add(PostbackEvent)
    def handle_postback(event):
        print("postbackevent: {}".format(event))
        service = api_manager.build_service()

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        eventsResult = service.events().list(
            calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
