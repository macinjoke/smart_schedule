import sys
from imp import reload

reload(sys)

from flask import render_template
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from smart_schedule.settings import db, app


@app.route("/")
def hello():
    return render_template("index.html")

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='localhost', port='8080'))

if __name__ == "__main__":
    manager.run()
