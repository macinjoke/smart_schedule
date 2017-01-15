# -*- coding: utf-8 -*-

from datetime import datetime

from flask import Flask
from linebot import (
    LineBotApi
)
from linebot.exceptions import (
    LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage,
    PostbackEvent,StickerSendMessage)

from smart_schedule.line.module import (
exit_confirm, post_carousel, get_join_contents_buttons
)
from smart_schedule.settings import line_env

app = Flask(__name__)

line_bot_api = LineBotApi(line_env['channel_access_token'])

keyword_flag = False

day_flag = False
up_day_flag = False

def handle(handler, body, signature):
    handler.handle(body, signature)

    @handler.add(MessageEvent, message = TextMessage)
    def handle_message(event):
        print(event)
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        global up_day_flag
        global day_flag
        global keyword_flag

        if day_flag:
            day_flag = False
            reply_text = "{}日後の予定を表示します".format(event.message.text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text = reply_text)
            )
            return -1

        if up_day_flag:
            up_day_flag = False
            reply_text = "{}日後までの予定を表示します".format(event.message.text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text = reply_text)
            )
            return -1

        if keyword_flag:
            keyword_flag = False
            reply_text="キーワードは、{}".format(event.message.text)
            # keyword = event.message.text.split('、')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text = reply_text)
            )
            return -1
        if event.message.text == "#menu":
            post_carousel(event.reply_token)
            return -1
        if not event.message.text.startswith("予定 "):
            if event.message.text.startswith("大好き"):
                reply_text = "大好きだよ！！！".format(event.message.text)
            elif event.message.text.startswith("退出") and not event.source.type=="user":
                confirm_message = TemplateSendMessage(
                    alt_text = 'Confirm template',
                    template = exit_confirm(time)
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
                TextSendMessage(text = reply_text)
            )
            return -1

        schedule_name = event.message.text.split(maxsplit = 1)[1]
        buttons_template_message = TemplateSendMessage(
            alt_text = 'Buttons template',
            template = get_join_contents_buttons(schedule_name, time)
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
        data = event.postback.data.split(',')
        print(data)
        print(data[1])
        pre_time = datetime.strptime(data[1],'%Y-%m-%d %H:%M:%S')
        compare = datetime.now()-pre_time
        print(compare)
        if(compare.total_seconds() < 20):
            if data[0] == "yes" and event.source.type == "group":
                try:
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id = "2", sticker_id = "42")
                    )
                    line_bot_api.leave_group(event.source.group_id)
                except LineBotApiError as e:
                    print(e)
            elif data[0] == "yes" and event.source.type == "room":
                print("OK")
                try:
                    line_bot_api.reply_message(
                        event.reply_token,
                        StickerSendMessage(package_id = "2" ,sticker_id = "42")
                    )
                    line_bot_api.leave_room(event.source.room_id)
                except LineBotApiError as e:
                    print(e)
            elif data[0] == "no":
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = "退出をキャンセルします。")
                )
            elif data[0] == "#keyword_search":
                global flag
                flag = True
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = "キーワードを入力してください\n例：バイト、研究室")
                )
            elif data[0] == "#after n days_schedule":
                global day_flag
                day_flag = True
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(text = "n日後の予定を表示します"),
                        TextSendMessage(text = "何日後の予定を表示しますか？\n例：5")
                    ]
                )
            elif data[0] == "#up to n days_schedule":
                global up_day_flag
                up_day_flag = True
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(
                            text = "n日後までの予定を表示します"
                        ),
                        TextSendMessage(
                            text = "何日後までの予定を表示しますか？\n例：5"
                        )
                    ]
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text = "タイムアウトです。\nもう一度最初からやり直してください")
            )
