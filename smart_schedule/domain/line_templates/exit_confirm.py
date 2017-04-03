from linebot.models import ConfirmTemplate, PostbackTemplateAction


class ExitConfirm(ConfirmTemplate):

    def __init__(self, time, messages):
        self.id = self.__class__.__name__
        text = messages['text']
        actions = [
            PostbackTemplateAction(
                label=messages['actions'][0]['label'],
                data='{}_yes,{}'.format(self.id, time)
            ),
            PostbackTemplateAction(
                label=messages['actions'][1]['label'],
                data='{}_no,{}'.format(self.id, time)
            )
        ]
        super(ExitConfirm, self).__init__(
            text=text, actions=actions
        )
