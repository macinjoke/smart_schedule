from flask import Flask, request, abort

from linebot import WebhookHandler
from linebot.exceptions import (
    InvalidSignatureError
)

from smart_schedule.settings import line_env

from smart_schedule.line import event_handler

app = Flask(__name__)

handler = WebhookHandler(line_env['channel_secret'])


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        event_handler.handle(handler, body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    app.run()
