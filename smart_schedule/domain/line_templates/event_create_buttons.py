from linebot.models import ButtonsTemplate, PostbackTemplateAction


class EventCreateButtons(ButtonsTemplate):

    #TODO textとdatesの両方を渡すのは冗長かも
    def __init__(self, time, messages, text, dates):
        self.id = self.__class__.__name__
        actions = [
            PostbackTemplateAction(
                label="{}/{}".format(date.month, date.day),
                data="{}_#create-calendar,{}/{},{}".format(
                    self.id, date.month, date.day, time
                )
            ) for date in dates
        ]
        reply_text = '{}\n{}'.format(text, messages['text'])
        super(EventCreateButtons, self).__init__(
            text=reply_text, actions=actions
        )
