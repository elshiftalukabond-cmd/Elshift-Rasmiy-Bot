import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler # YANGI QO'SHILDI
from config import BOT_TOKEN
from handlers import router
from scheduler import setup_scheduler # YANGI QO'SHILDI

logger = logging.getLogger(__name__)

async def main():
    logger.info("[MAIN] Bot sozlanmoqda...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    logger.info("[MAIN] Router ulanmoqda...")
    dp.include_router(router)

    # ===================================================
    # SCHEDULER NI ISHGA TUSHIRISH (O'ZBEKISTON VAQTI BILAN)
    # ===================================================
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    setup_scheduler(scheduler, bot)
    scheduler.start()
    logger.info("[SCHEDULER] Vaqtni kuzatish tizimi ishga tushdi.")
    # ===================================================

    print("🚀 Elshift Logistika boti ishga tushmoqda...")
    logger.info("[MAIN] Webhooklar tozalanmoqda va Polling boshlanmoqda...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        logger.info("[MAIN] Bot ishlashni to'xtatdi, sessiya yopilmoqda...")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot to'xtatildi")