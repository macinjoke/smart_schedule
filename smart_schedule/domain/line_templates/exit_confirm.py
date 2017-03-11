
from linebot.models import ConfirmTemplate, PostbackTemplateAction
from . import Type


class ExitConfirm(ConfirmTemplate):

    TYPE = Type.CONFIRM

    def __init__(self, time, messages):
        text = messages['text']
        actions = [
            PostbackTemplateAction(
                label=messages['actions'][0]['label'],
                data='exit_yes,{}'.format(time)
            ),
            PostbackTemplateAction(
                label=messages['actions'][1]['label'],
                data='exit_yes,{}'.format(time)
            )
        ]
        super(ConfirmTemplate, self).__init__(
            type=ExitConfirm.TYPE, text=text, actions=actions
        )
