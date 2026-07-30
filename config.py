import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.environ.get("DB_HOST",     "localhost")
DB_USER     = os.environ.get("DB_USER",     "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "@puni")
DB_NAME     = os.environ.get("DB_NAME",     "villagepay")
