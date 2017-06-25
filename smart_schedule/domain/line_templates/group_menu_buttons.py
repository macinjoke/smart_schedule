from linebot.models import ButtonsTemplate, PostbackTemplateAction


class GroupMenuButtons(ButtonsTemplate):

    def __init__(self, time, messages):
        self.id = self.__class__.__name__
        text = messages['text']
        title = messages['title']
        actions = [
            PostbackTemplateAction(
                label=messages['actions'][0]['label'],
                data='{}_#adjust,{}'.format(self.id, time)
            ),
            PostbackTemplateAction(
                label=messages['actions'][1]['label'],
                data='{}_#member,{}'.format(self.id, time)
            ),
            PostbackTemplateAction(
                label=messages['actions'][2]['label'],
                data='{}_#g-calender,{}'.format(self.id, time)
            )
        ]
        super(GroupMenuButtons, self).__init__(
            title=title, text=text, actions=actions
        )
