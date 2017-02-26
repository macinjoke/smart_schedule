# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Unicode, UnicodeText, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()


class Personal(db.Model):
    """
    個人情報格納のモデル
    """
    __tablename__ = "personal_info"
    id = Column(Integer, primary_key=True)
    user_id = Column(Unicode(255))
    credential = Column(Unicode(1200))
    up_to_day_flag = Column(Boolean)
    day_flag = Column(Boolean)
    keyword_flag = Column(Boolean)
    adjust_flag = Column(Boolean)
    users = relationship("GroupUser")

    # 生成された時に呼び出される
    def __init__(self, user_id, credential):
        self.user_id = user_id
        self.credential = credential
        self.up_to_day_flag = False
        self.day_flag = False
        self.keyword_flag = False
        self.adjust_flag = False


class GroupUser(db.Model):
    """
    グループトーク内のユーザー
    """
    __tablename__ = "group_user"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(20))
    group_id = Column(Integer, ForeignKey('personal_info.id'))
    free_days = relationship("FreeDay")

    def __init__(self, name, group_id):
        self.name = name
        self.group_id = group_id


class FreeDay(db.Model):
    """
    日程調整機能における空いている日
    """
    __tablename__ = "free_day"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    user_id = Column(Integer, ForeignKey('group_user.id'))

    def __init__(self, date, user_id):
        self.data = date
        self.user_id = user_id
