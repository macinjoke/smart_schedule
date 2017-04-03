# -*- coding: utf-8 -*-

import json
from datetime import datetime
import requests

from smart_schedule.settings import line_env


def post_carousel(reply_token):
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header = {
        "Content-Type": "application/json",
        "Authorization": 'Bearer ' + line_env['channel_access_token']
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "template",
                "altText": "Carousel template",
                "template": {
                    "type": "carousel",
                    "columns":
                        [
                            {
                                "title": "予定を見る",
                                "text": "選択してください",
                                "actions": [
                                    {
                                        "type": "postback",
                                        "label": "今日の予定を表示",
                                        "data": "#today_schedule,{}".format(time)
                                    },
                                    {
                                        "type": "postback",
                                        "label": "明日の予定を表示",
                                        "data": "#tomorrow_schedule,{}".format(time)
                                    },
                                    {
                                        "type": "postback",
                                        "label": "1週間後までの予定を表示",
                                        "data": "#7days_schedule,{}".format(time)
                                    },
                                ]
                            },
                            {
                                "title": "予定を見る",
                                "text": "よりスマートな検索",
                                "actions":
                                    [
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

                        ]
                }
            }
        ]
    }
    requests.post('https://api.line.me/v2/bot/message/reply', headers=header, data=json.dumps(payload))
