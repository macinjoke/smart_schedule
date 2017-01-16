import sys
from imp import reload

reload(sys)

import os
from flask import Flask, render_template
from smart_schedule.models import db
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)
#デバッグ
app.config['DEBUG'] = True
#秘密キー
app.secret_key = 'development key'
#データベースを指定
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_NATIVE_UNICODE'] = 'utf-8'
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