from linebot.models import JoinEvent, TextSendMessage
from . import line_bot_api


class JoinEventHandler:

    def __init__(self, handler):
        self.handler = handler

        @self.handler.add(JoinEvent)
        def handle(event):
            print(event)
            join_message = '''グループに招待ありがとうございます！
グループでは「予定調整機能」「グループに登録されたカレンダーの予定確認」ができます。
詳しい使い方はアカウント紹介ページを見てください。
グループで使用できるコマンドを呼び出すメッセージは「help」と送信すると見ることができます。'''
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=join_message)
            )
