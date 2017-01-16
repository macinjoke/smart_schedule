# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Unicode, UnicodeText, ForeignKey, Boolean
from sqlalchemy.orm import relationships,backref
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

    # 生成された時に呼び出される
    def __init__(self, user_id, credential):
        self.user_id = user_id
        self.credential = credential
        self.up_to_day_flag = False
        self.day_flag = False
        self.keyword_flag = False
