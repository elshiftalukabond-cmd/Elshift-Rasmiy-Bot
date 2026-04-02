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
GOOGLE_CREDENTIALS_JSON_PATH = os.getenv("GOOGLE_CREDENTIALS_JSON_PATH")
SHEET_NAME = "Elshift"

try:
    LOGIST_GROUP_ID = int(os.getenv("LOGIST_GROUP_ID", 0))
    ABOUT_US_MSG_ID = int(os.getenv("ABOUT_US_MSG_ID", 0))
    CONTACT_MSG_ID = int(os.getenv("CONTACT_MSG_ID", 0))
    NEW_CLIENT_INFO_MSG_ID = int(os.getenv("NEW_CLIENT_INFO_MSG_ID", 0)) # YANGI QO'SHILDI
except ValueError:
    LOGIST_GROUP_ID = 0
    ABOUT_US_MSG_ID = 0
    CONTACT_MSG_ID = 0
    NEW_CLIENT_INFO_MSG_ID = 0

if not all([BOT_TOKEN, GOOGLE_CREDENTIALS_JSON_PATH]) or LOGIST_GROUP_ID == 0:
    logger.critical("[CONFIG] DIQQAT: .env faylida ma'lumotlar yetishmayapti yoki xato!")
    exit(1)

try:
    LOGIST_GROUP_ID = int(os.getenv("LOGIST_GROUP_ID", 0))
    ABOUT_US_MSG_ID = int(os.getenv("ABOUT_US_MSG_ID", 0))
    CONTACT_MSG_ID = int(os.getenv("CONTACT_MSG_ID", 0))
    NEW_CLIENT_INFO_MSG_ID = int(os.getenv("NEW_CLIENT_INFO_MSG_ID", 0))
except ValueError:
    LOGIST_GROUP_ID = ABOUT_US_MSG_ID = CONTACT_MSG_ID = NEW_CLIENT_INFO_MSG_ID = 0

# --- WAKE SOZLAMALARI (FAQAT VAQTLAR) ---
WAKE_SCHEDULE_TIMES = os.getenv("WAKE_SCHEDULE_TIMES", "09:00,14:00,16:00").split(",")

if not all([BOT_TOKEN, GOOGLE_CREDENTIALS_JSON_PATH]) or LOGIST_GROUP_ID == 0:
    logger.critical("[CONFIG] DIQQAT: .env faylida ma'lumotlar yetishmayapti yoki xato!")
    exit(1)