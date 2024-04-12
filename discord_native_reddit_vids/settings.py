import logging
import os
import dotenv
import pathlib

dotenv.load_dotenv()

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s]%(name)s: %(message)s",
)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

BASE_DIR = pathlib.Path(__file__).parent.parent

TMP_DIR = BASE_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_VIDEO_SIZE = 8 * 1024 * 1024
MAX_DURATION = 60 * 15

HOST_URL = os.getenv("HOST_URL", "http://localhost:8000")

COOKIE_FILE_PATH = BASE_DIR / "cookies.txt"