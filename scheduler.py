import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from google_sheets import repo
from keyboards import get_wake_confirm_keyboard
from config import WAKE_SCHEDULE_TIMES

logger = logging.getLogger(__name__)

async def send_wake_to_user(bot: Bot, tg_id: int, name: str, time_str: str):
    kb = get_wake_confirm_keyboard(time_str)
    text = f"🔔 <b>SO'ROVNOMA!</b>\n\nHurmatli <b>{name}</b>,\nHozirgi ({time_str}) holatiga ko'ra, siz mas'ul bo'lgan obyektlarda <b>Kirim</b> yoki <b>Chiqim</b> mavjudmi?"
    
    try:
        await bot.send_message(chat_id=tg_id, text=text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.error(f"Xodim {name} ga wake yuborishda xato: {e}")

async def job_wake_request(bot: Bot, time_str: str):
    logger.info(f"[WAKE] {time_str} dagi so'rovlar boshlandi...")
    users = await asyncio.to_thread(repo.get_wake_employees)
    
    for u in users:
        await send_wake_to_user(bot, u['tg_id'], u['full_name'], time_str)

def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot):
    # .env dagi belgilangan vaqtlar uchun jadvallarni tuzamiz
    for time_str in WAKE_SCHEDULE_TIMES:
        time_str = time_str.strip()
        if ":" in time_str:
            hour, minute = time_str.split(":")
            scheduler.add_job(job_wake_request, 'cron', hour=int(hour), minute=int(minute), args=[bot, time_str])
            logger.info(f"[SCHEDULER] Wake so'rovi sozlandi: Soat {hour}:{minute} ga.")