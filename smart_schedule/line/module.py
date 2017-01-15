# -*- coding: utf-8 -*-

import json
from datetime import datetime

import requests
from linebot.models import (
    PostbackTemplateAction, MessageTemplateAction, URITemplateAction, ButtonsTemplate,
    ConfirmTemplate)

from smart_schedule.settings import line_env

def exit_confirm(time):
    return ConfirmTemplate(
        text="本当に退出させますか？",
        actions=[
            PostbackTemplateAction(
                label='Yes',
                data='yes,{}'.format(time)
            ),
            PostbackTemplateAction(
                label='No',
                data='no,{}'.format(time)
            )
        ]
    )


def buttons(schedule_name, time):
    return ButtonsTemplate(
        # 芝刈り機のイラスト
        thumbnail_image_url='https://2.bp.blogspot.com/-SObo8z0Ajyw/V9ppuyMxT2I/AAAAAAAA9xI/jwNeixWhDeMJ6K_z96edB45umM6WTftVQCLcB/s800/kusakari_shibakari.png',
        title="{} の予定".format(schedule_name),
        text="選択してね",
        actions=[
            PostbackTemplateAction(
                label='参加する',
                data='join,{}'.format(time)
            ),
            PostbackTemplateAction(
                label='参加しない',
                data='nojoin,{}'.format(time)
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

def post_carousel(reply_token):
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header = {
        "Content-Type": "application/json",
        "Authorization": 'Bearer ' + line_env['channel_access_token']
    }
    payload = {
          "replyToken":reply_token,
          "messages":[
              {
                "type": "template",
                "altText": "Carousel template",
                "template": {
                    "type": "carousel",
                    "columns": [

                        {
                          # "thumbnailImageUrl": "https://2.bp.blogspot.com/-SObo8z0Ajyw/V9ppuyMxT2I/AAAAAAAA9xI/jwNeixWhDeMJ6K_z96edB45umM6WTftVQCLcB/s800/kusakari_shibakari.png",
                          "title": "自分の予定を見る",
                          "text": "選択してください",
                          "actions": [

                              {
                                  "type": "postback",
                                  "label": "キーワード検索",
                                  "data": "#keyword_search,{}".format(time)
                              },
                              {
                                  "type": "postback",
                                  "label": "n日後の予定を表示",
                                  "data": "#after n days_schedule,{}".format(time)
                              },
                              {
                                  "type": "postback",
                                  "label": "n日後までの予定を表示",
                                  "data": "#up to n days_schedule,{}".format(time)
                              },
                          ]
                        },
                        {
                          # "thumbnailImageUrl": "https://2.bp.blogspot.com/-SObo8z0Ajyw/V9ppuyMxT2I/AAAAAAAA9xI/jwNeixWhDeMJ6K_z96edB45umM6WTftVQCLcB/s800/kusakari_shibakari.png",
                          "title": "予定を追加する",
                          "text": "選択してください",
                          "actions": [

                              {
                                  "type": "uri",
                                  "label": "詳細を見る",
                                  "uri": "http://example.com"
                              },
                              {
                                  "type": "uri",
                                  "label": "詳細を見る",
                                  "uri": "http://example.com"
                              },
                              {
                                  "type": "uri",
                                  "label": "詳細を見る",
                                  "uri": "http://example.com"
                              },
                          ]
                        },

                    ]
                }
              }
            ]
    }
    requests.post('https://api.line.me/v2/bot/message/reply', headers=header, data=json.dumps(payload))