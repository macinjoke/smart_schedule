import sys
from imp import reload

reload(sys)

import os
from flask import Flask, render_template
from smart_schedule.models import db
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from flask_session import SqlAlchemySessionInterface
from smart_schedule.settings import db_env

app = Flask(__name__)
# デバッグ
app.config['DEBUG'] = True
# 秘密キー
app.secret_key = 'development key'
# データベースを指定
app.config['SQLALCHEMY_DATABASE_URI'] = db_env['database_url']
app.config['SQLALCHEMY_NATIVE_UNICODE'] = 'utf-8'
# flaskのsessionモデルを追加
SqlAlchemySessionInterface(app=app, db=db, table='sessions', key_prefix='user')
db.init_app(app)
db.app = app


@app.route("/")
def hello():
    return render_template("index.html")

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='localhost', post='8080'))

if __name__ == "__main__":
    manager.run()