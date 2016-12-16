from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage,
    PostbackTemplateAction, MessageTemplateAction, URITemplateAction, ButtonsTemplate)

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "Ntaj7mJX7ND9t/w/oyx2AHswL/Sw2SeQov8nXnuBrHOAm/Z/GprbxZ7/RAzcSNEEYkU3Jqt5o8ded9wvNP+F+sgZFdtV2wos8kcAk9ooV3VdS5V7eg7k1hR68GKNXb2fQ++vvjBqB7S7Tlq2UnFhRQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "35bd4afd5d85a5ae77a1d84aa3cfb7ec"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    button_template_text = "ん？ {} ってどうゆう意味? ".format(event.message.text)
    buttons_template_message = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            # 芝刈り機のイラスト
            thumbnail_image_url='https://2.bp.blogspot.com/-SObo8z0Ajyw/V9ppuyMxT2I/AAAAAAAA9xI/jwNeixWhDeMJ6K_z96edB45umM6WTftVQCLcB/s800/kusakari_shibakari.png',
            title='Menu',
            text=button_template_text,
            actions=[
                PostbackTemplateAction(
                    label='postback',
                    text='postback text',
                    data='action=buy&itemid=1'
                ),
                MessageTemplateAction(
                    label='message',
                    text='message text'
                ),
                URITemplateAction(
                    label='uri',
                    uri='http://example.com/'
                )
            ]
        )
    )
    # text_send_message = TextSendMessage(text=reply_text)
    line_bot_api.reply_message(
        event.reply_token,
        buttons_template_message
    )


if __name__ == "__main__":
    app.run()