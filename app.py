import sys

sys.path.append('/home/Dhanushliebe/support_ticket/')
import telebot
from flask import Flask
from Events import socketio
from src import get_config


application = app = Flask(__name__, static_folder='assets', static_url_path="/")
app.secret_key = get_config("secret_key")
app.debug = True

TOKEN = get_config("bot_token")
admin_user = get_config("admin")
bot = telebot.TeleBot(TOKEN, parse_mode=None)
socketio.init_app(app)

from blueprint import telegram , files,  home , user , ticket

app.register_blueprint(telegram.bp)
app.register_blueprint(user.bp)
app.register_blueprint(files.bp)
app.register_blueprint(home.bp)
app.register_blueprint(ticket.bp)


if __name__ == '__main__':
   socketio.run(app, host='0.0.0.0', port=5000, debug=True)

