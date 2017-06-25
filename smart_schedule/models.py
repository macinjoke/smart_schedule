from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Column, Integer, Unicode, ForeignKey, Boolean, Date, UniqueConstraint
)
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class Talk(db.Model):
    """
    ユーザーや、グループ、トークルームを表す
    """
    __tablename__ = "talk"
    id = Column(Integer, primary_key=True)
    talk_id = Column(Unicode(255), unique=True)
    credential = Column(Unicode(1200))
    calendar_id = Column(Unicode(200))
    up_to_day_flag = Column(Boolean)
    day_flag = Column(Boolean)
    date_flag = Column(Boolean)
    keyword_flag = Column(Boolean)
    calendar_select_flag = Column(Boolean)
    free_days = relationship("FreeDay")

    # 生成された時に呼び出される
    def __init__(self, talk_id, credential):
        self.talk_id = talk_id
        self.credential = credential
        self.calendar_id = 'primary'
        self.up_to_day_flag = False
        self.day_flag = False
        self.date_flag = False
        self.keyword_flag = False
        self.calendar_select_flag = False


class FreeDay(db.Model):
    """
    日程調整機能における空いている日
    """
    __tablename__ = "free_day"
    __table_args__ = (
        UniqueConstraint(
            'date', 'user_name', 'talk_id',
            name='_date_user_name_talk_id_uc'
        ),
    )
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    user_name = Column(Unicode(255))
    talk_id = Column(Integer, ForeignKey('talk.id'))

    def __init__(self, date, user_name, talk_id):
        self.date = date
        self.user_name = user_name
        self.talk_id = talk_id
