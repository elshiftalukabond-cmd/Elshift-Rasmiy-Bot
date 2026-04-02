import os
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("[CONFIG] .env faylidan muhit o'zgaruvchilari yuklanmoqda...")
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# DIQQAT: Bu yerdan _PATH so'zi olib tashlandi
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
SHEET_NAME = "Elshift"

try:
    LOGIST_GROUP_ID = int(os.getenv("LOGIST_GROUP_ID", 0))
    ABOUT_US_MSG_ID = int(os.getenv("ABOUT_US_MSG_ID", 0))
    CONTACT_MSG_ID = int(os.getenv("CONTACT_MSG_ID", 0))
    NEW_CLIENT_INFO_MSG_ID = int(os.getenv("NEW_CLIENT_INFO_MSG_ID", 0))
except ValueError:
    LOGIST_GROUP_ID = ABOUT_US_MSG_ID = CONTACT_MSG_ID = NEW_CLIENT_INFO_MSG_ID = 0

WAKE_SCHEDULE_TIMES = os.getenv("WAKE_SCHEDULE_TIMES", "09:00,14:00,16:00").split(",")

# DIQQAT: Bu yerda ham _PATH so'zi olib tashlandi
if not all([BOT_TOKEN, GOOGLE_CREDENTIALS_JSON]) or LOGIST_GROUP_ID == 0:
    logger.critical("[CONFIG] DIQQAT: muhit o'zgaruvchilari (Variables) yetishmayapti yoki xato!")
    exit(1)