from pathlib import Path
from environs import Env


env = Env()
env.read_env(override=True)

secret_key = env.str('SECRET_KEY')
is_debug = env.bool('IS_DEBUG', False)
github_webhook_secret = env.str('GITHUB_WEBHOOK_SECRET', None)

db_name = env.str('DB_NAME')
db_username = env.str('DB_USERNAME')
db_password = env.str('DB_PASSWORD')
db_host = env.str('DB_HOST')
db_port = env.int('DB_PORT')

iiko_host = env.str('IIKO_API_SERVER')
iiko_username = env.str('IIKO_API_USERNAME')
iiko_password = env.str('IIKO_API_PASSWORD')

bot_token = env.str('BOT_TOKEN')

data_dir = env.str(
    'DATA_DIR',
    default=Path(__file__).resolve().parent.parent / 'data'
)
