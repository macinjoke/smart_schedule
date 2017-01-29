import os
from dotenv import load_dotenv

APP_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, '..'))

dotenv_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

line_env = {
    'channel_access_token': os.environ.get('CHANNEL_ACCESS_TOKEN'),
    'channel_secret': os.environ.get('CHANNEL_SECRET'),
    'user_id': os.environ.get("LINE_USER_ID")
}

db_env = {
    'database_url': os.environ.get('DATABASE_URL')
}

web_env = {
    'host': os.environ.get('WEB_SERVER_HOST')
}

hash_env = {
    'seed': os.environ.get('HASH_SEED')
}
