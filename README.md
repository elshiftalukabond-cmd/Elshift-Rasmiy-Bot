# Elshift Logistika Boti (PRO Versiya)

Ushbu Telegram bot kompaniya logistlari uchun maxsus ishlab chiqilgan. Bot Google Sheets bilan integratsiya qilingan bo'lib, barcha ma'lumotlarni asinxron tarzda o'qiydi va yozadi. 

## Arxitektura (Inline & ID-based)
Dastur tezligi va masshtablash (scalability) qobiliyatini oshirish uchun **Stateless** (holatsiz) yondashuv qo'llanilgan. Obyektlar nomi bilan emas, faqat ularning yagona **ID (oid)** raqami bilan ishlaydi. Barcha amallar Inline tugmalar yordamida `callback_data` (masalan, `deliver_102`) orqali boshqariladi.

## Texnologiyalar
* **Python 3.9+**
* **Aiogram 3.x** (Asinxron Telegram freymvork)
* **Gspread** (Google Sheets API)
* **Asyncio** (`asyncio.to_thread` orqali API so'rovlar asosiy oqimni to'smaydi)

## Fayllar strukturasi
1. `.env` - Maxfiy kalitlar va bot tokenlari.
2. `config.py` - Sozlamalarni yuklovchi modul.
3. `models.py` - Google Sheets'dan kelgan qatorlarni obyektlarga aylantiruvchi klasslar.
4. `google_sheets.py` - API bilan ishlovchi asosiy Repozitoriy (Faqat Logist logikasi qoldirilgan).
5. `keyboards.py` - Inline va Reply tugmalar.
6. `handlers.py` - Foydalanuvchi so'rovlarini qabul qiluvchi kontrollerlar.
7. `main.py` - Botni ishga tushiruvchi asosiy fayl.

## Ishga tushirish
1. `requirements.txt` dagi kutubxonalarni o'rnating: `pip install -r requirements.txt`
2. `.env` faylida va `elshift-telegram-scheduler.json` faylida o'z ma'lumotlaringizni to'ldiring.
3. Botni ishga tushiring: `python main.py`