from smart_schedule import http, line
from smart_schedule.settings import app

event_handler = line.EventHandler()
flask_main = http.FlaskMain(app, event_handler.handler)
# gunicorn から読ませるために変数appに代入
app = flask_main.app

if __name__ == "__main__":
    app.run()
