import asyncio
from datetime import datetime
from config import LOGIST_GROUP_ID, ABOUT_US_MSG_ID, CONTACT_MSG_ID, NEW_CLIENT_INFO_MSG_ID
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from google_sheets import repo
from keyboards import (
    get_main_public_menu, get_contact_keyboard, get_logist_main_menu, 
    get_objects_reply_keyboard, get_object_action_reply_keyboard, 
    get_cancel_process_keyboard, get_confirm_delivery_keyboard,
    get_client_objects_reply_keyboard, get_client_object_action_reply_keyboard, KeyboardButton,
    get_admin_main_menu, get_wake_more_keyboard
)
from models import TgUserStatus
import logging

logger = logging.getLogger(__name__)
router = Router()

class DeliveryState(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_video = State()

class AuthState(StatesGroup):
    waiting_for_logist_contact = State()
    waiting_for_client_contact = State()
    waiting_for_admin_contact = State()

class WakeState(StatesGroup):
    waiting_for_report = State()

@router.message(Command("start"))
async def cmd_public_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>Elshift rasmiy botiga xush kelibsiz!</b>\n\nQuyidagi menyudan kerakli bo'limni tanlang:",
        parse_mode="HTML", reply_markup=get_main_public_menu()
    )

@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us_handler(message: Message):
    if ABOUT_US_MSG_ID:
        try:
            await message.bot.copy_message(chat_id=message.from_user.id, from_chat_id=LOGIST_GROUP_ID, message_id=ABOUT_US_MSG_ID)
        except Exception:
            await message.answer("⚠️ Ma'lumotlarni yuklashda xatolik yuz berdi.")
    else:
        await message.answer("Tez orada ma'lumot qo'shiladi.")

@router.message(F.text == "📍 Manzil va Aloqa")
async def contact_info_handler(message: Message):
    if CONTACT_MSG_ID:
        try:
            await message.bot.copy_message(chat_id=message.from_user.id, from_chat_id=LOGIST_GROUP_ID, message_id=CONTACT_MSG_ID)
        except Exception:
            await message.answer("⚠️ Ma'lumotlarni yuklashda xatolik yuz berdi.")
    else:
        await message.answer("Tez orada ma'lumot qo'shiladi.")

@router.message(F.text == "💼 Bo'sh ish o'rinlari")
async def vacancies_handler(message: Message):
    await message.answer("💼 Hozirgi vaqtda ochiq vakansiyalar mavjud emas. Yangiliklarni kuzatib boring!", parse_mode="HTML")

@router.message(F.text == "🤝 Mijozlar bo'limi")
async def cmd_client_login(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AuthState.waiting_for_client_contact)
    await message.answer(
        "🤝 <b>Mijozlar bo'limiga xush kelibsiz!</b>\n\nShaxsingizni tasdiqlash uchun pastdagi tugma orqali telefon raqamingizni yuboring.",
        parse_mode="HTML", reply_markup=get_contact_keyboard()
    )

@router.message(F.contact, AuthState.waiting_for_client_contact)
async def handle_client_contact(message: Message, state: FSMContext):
    raw_phone = message.contact.phone_number
    telegram_id = message.from_user.id
    
    digits_only = "".join(filter(str.isdigit, str(raw_phone)))
    clean_phone_9 = digits_only[-9:] if len(digits_only) >= 9 else digits_only
    
    admin_phone_format = f"+998{clean_phone_9}"
    
    status_msg = await message.answer("Baza tekshirilmoqda... ⏳", reply_markup=ReplyKeyboardRemove())
    client = await asyncio.to_thread(repo.auth_client, raw_phone, telegram_id)
    await status_msg.delete()
    
    if client.tg_status == "Topilmadi":
        full_name = message.from_user.full_name
        username = message.from_user.username or "yo'q"
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        await asyncio.to_thread(repo.save_new_client_attempt, str(telegram_id), clean_phone_9, full_name, username, now_str)
        
        admin_ids = await asyncio.to_thread(repo.get_all_admins_tg_ids)
        alert_text = (
            f"🚨 <b>DIQQAT: Yangi mijoz urinishi!</b>\n\n"
            f"👤 <b>F.I.O:</b> {full_name}\n"
            f"📞 <b>Tel:</b> {admin_phone_format}\n"
            f"💬 <b>Username:</b> @{username}\n"
            f"📅 <b>Sana:</b> {now_str}\n\n"
            f"<i>Ushbu mijoz ma'lumotlari 'YangiMijoz' jadvaliga saqlandi.</i>"
        )
        for adm_id in admin_ids:
            try:
                await message.bot.send_message(chat_id=adm_id, text=alert_text, parse_mode="HTML")
            except Exception:
                pass 

    
        if NEW_CLIENT_INFO_MSG_ID:
            try:
                await message.bot.copy_message(chat_id=telegram_id, from_chat_id=LOGIST_GROUP_ID, message_id=NEW_CLIENT_INFO_MSG_ID, reply_markup=get_main_public_menu())
            except Exception as e:
                logger.error(f"Yangi mijozga info yuborishda xato: {e}")
                await message.answer("Sizning ma'lumotlaringiz bazadan topilmadi. Iltimos, operator bilan bog'laning.", reply_markup=get_main_public_menu())
        else:
            await message.answer("Sizning ma'lumotlaringiz bazadan topilmadi. Iltimos, operator bilan bog'laning.", reply_markup=get_main_public_menu())

    elif client.tg_status.lower() == TgUserStatus.APPROVED:
        await state.clear()
        await state.update_data(user_role="client", client_cid=client.cid)
        
        wait_msg = await message.answer("Ma'lumotlar yuklanmoqda... ⏳")
        projects = await asyncio.to_thread(repo.get_client_objects, client.cid)
        await wait_msg.delete()
        
        if not projects:
            kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🚪 Tizimdan chiqish")]], resize_keyboard=True)
            await message.answer(
                f"✅ <b>Hurmatli {client.name}, shaxsiy kabinetingizga xush kelibsiz!</b>\n\nSizga biriktirilgan faol obyektlar topilmadi.", 
                parse_mode="HTML", reply_markup=kb
            )
            return

        objects_map = {p.name: p.oid for p in projects}
        await state.update_data(client_objects_map=objects_map)
        
        await message.answer(
            f"✅ <b>Hurmatli {client.name}, shaxsiy kabinetingizga xush kelibsiz!</b>\n\n🏢 <b>Qaysi obyekt bo'yicha ma'lumot ko'rmoqchisiz?</b>",
            parse_mode="HTML", reply_markup=get_client_objects_reply_keyboard(projects)
        )
    else:
        await message.answer(f"⏳ Statusingiz: {client.tg_status}. Admin tasdiqlashini kuting.", reply_markup=get_main_public_menu())


@router.message(Command("elshift_logist"))
async def cmd_logist_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AuthState.waiting_for_logist_contact)
    await message.answer(
        "🔐 <b>Elshift Logistika tizimiga xush kelibsiz!</b>\n\nTelefon raqamingizni yuboring.",
        parse_mode="HTML", reply_markup=get_contact_keyboard()
    )

@router.message(Command("elshift_admin"))
async def cmd_admin_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AuthState.waiting_for_admin_contact)
    await message.answer(
        "🛠 <b>Elshift Boshqaruv (Admin) tizimiga xush kelibsiz!</b>\n\nTelefon raqamingizni yuboring.",
        parse_mode="HTML", reply_markup=get_contact_keyboard()
    )

@router.message(F.contact, AuthState.waiting_for_logist_contact)
async def handle_logist_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    
    status_msg = await message.answer("Baza tekshirilmoqda... ⏳", reply_markup=ReplyKeyboardRemove())
    employee = await asyncio.to_thread(repo.auth_employee, phone, telegram_id, expected_role="logist")
    await status_msg.delete()
    
    if employee.tg_status == TgUserStatus.NOT_FOUND:
        await message.answer("❌ Ma'lumotlaringiz topilmadi.", reply_markup=get_main_public_menu())
    elif employee.tg_status == "Lavozim Xato":
        await message.answer("⛔ Lavozimingiz 'Logist' emas.", reply_markup=get_main_public_menu())
    elif employee.tg_status.lower() == TgUserStatus.APPROVED:
        await state.clear()
        await state.update_data(user_role="logist", emp_id=employee.emp_id)
        await message.answer(f"✅ <b>Profilga kirdingiz!</b>\n\n👤 {employee.full_name}\n💼 {employee.lavozim}", parse_mode="HTML", reply_markup=get_logist_main_menu())
    else:
        await message.answer(f"⏳ Statusingiz: {employee.tg_status}.", reply_markup=get_main_public_menu())

@router.message(F.contact, AuthState.waiting_for_admin_contact)
async def handle_admin_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    
    status_msg = await message.answer("Baza tekshirilmoqda... ⏳", reply_markup=ReplyKeyboardRemove())
    employee = await asyncio.to_thread(repo.auth_employee, phone, telegram_id, expected_role="admin")
    await status_msg.delete()
    
    if employee.tg_status == TgUserStatus.NOT_FOUND:
        await message.answer("❌ Ma'lumotlaringiz topilmadi.", reply_markup=get_main_public_menu())
    elif employee.tg_status == "Lavozim Xato":
        await message.answer("⛔ Sizda Admin huquqi yo'q.", reply_markup=get_main_public_menu())
    elif employee.tg_status.lower() == TgUserStatus.APPROVED:
        await state.clear()
        await state.update_data(user_role="admin", emp_id=employee.emp_id)
        await message.answer(f"✅ <b>Admin profiliga kirdingiz!</b>\n\n👤 {employee.full_name}", parse_mode="HTML", reply_markup=get_admin_main_menu())
    else:
        await message.answer(f"⏳ Statusingiz: {employee.tg_status}.", reply_markup=get_main_public_menu())

@router.message(F.text == "🚪 Tizimdan chiqish")
async def exit_system(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Siz asosiy menyuga qaytdingiz.", reply_markup=get_main_public_menu())

@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("user_role")
    
    if role == "logist":
        await message.answer("Logist menyusiga qaytdingiz.", reply_markup=get_logist_main_menu())
    elif role == "admin":
        await message.answer("Admin menyusiga qaytdingiz.", reply_markup=get_admin_main_menu())
    else:
        await state.clear()
        await message.answer("Asosiy menyuga qaytdingiz.", reply_markup=get_main_public_menu())

@router.message(F.text == "🔄 Yangilash")
async def admin_refresh_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("user_role") != "admin": return
    
    wait_msg = await message.answer("So'nggi 48 soat ichidagi urinishlar tekshirilmoqda... ⏳")
    recent_clients = await asyncio.to_thread(repo.get_recent_new_clients)
    await wait_msg.delete()
    
    if not recent_clients:
        return await message.answer("So'nggi 2 kun ichida yangi mijozlar tizimga kirishga urinmagan.", reply_markup=get_admin_main_menu())
        
    text = "📋 <b>Oxirgi 48 soatdagi yangi mijozlar:</b>\n\n"
    for i, c in enumerate(recent_clients, 1):
        display_phone = f"+998{c['phone']}" if len(c['phone']) == 9 else c['phone']
        text += f"<b>{i}.</b> 👤 {c['full_name']}\n📞 {display_phone} | @{c['username']}\n📅 {c['date_time']}\n\n"
        
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_menu())

@router.message(F.text == "🏢 Obyektlar")
@router.message(F.text == "🔙 Obyektlar ro'yxatiga")
async def show_objects_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("user_role")
    
    await state.update_data(current_oid=None, current_obj_name=None, current_cid=None)
    wait_msg = await message.answer("Obyektlar yuklanmoqda... ⏳", reply_markup=ReplyKeyboardRemove())
    
    if role == "logist":
        projects = await asyncio.to_thread(repo.get_active_objects)
        await wait_msg.delete()
        if not projects:
            return await message.answer("Faol obyektlar topilmadi.", reply_markup=get_logist_main_menu())
        objects_map = {f"{p.name} ({p.client_name})": p.oid for p in projects}
        await state.update_data(logist_objects_map=objects_map)
        await message.answer("🏢 <b>Qaysi obyekt bo'yicha amal bajarasiz?</b>", parse_mode="HTML", reply_markup=get_objects_reply_keyboard(projects))
        
    elif role == "client":
        cid = data.get("client_cid")
        projects = await asyncio.to_thread(repo.get_client_objects, cid)
        await wait_msg.delete()
        if not projects:
            kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🚪 Tizimdan chiqish")]], resize_keyboard=True)
            return await message.answer("Sizga biriktirilgan faol obyektlar topilmadi.", reply_markup=kb)
        objects_map = {p.name: p.oid for p in projects}
        await state.update_data(client_objects_map=objects_map)
        await message.answer("🏢 <b>Qaysi obyekt bo'yicha ma'lumot ko'rmoqchisiz?</b>", parse_mode="HTML", reply_markup=get_client_objects_reply_keyboard(projects))


@router.message(F.text == "✅ Mahsulot yetkazildi")
async def start_delivery_process(message: Message, state: FSMContext):
    data = await state.get_data()
    oid = data.get("current_oid")
    if not oid: return await message.answer("⚠️ Obyekt tanlang.", reply_markup=get_logist_main_menu())
    await state.set_state(DeliveryState.waiting_for_text)
    await message.answer("📝 <b>1-qadam:</b> Mahsulotlar haqida matn yozing.", parse_mode="HTML", reply_markup=get_cancel_process_keyboard())

@router.message(F.text == "🔙 Bekor qilish")
async def cancel_delivery_process(message: Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("❌ Jarayon bekor qilindi.", reply_markup=get_object_action_reply_keyboard())

@router.message(DeliveryState.waiting_for_text, F.text)
async def process_delivery_text(message: Message, state: FSMContext):
    await state.update_data(delivery_text=message.text)
    await state.set_state(DeliveryState.waiting_for_photo)
    await message.answer("📸 <b>2-qadam:</b> Rasm yuklang.", parse_mode="HTML")

@router.message(DeliveryState.waiting_for_photo, F.photo)
async def process_delivery_photo(message: Message, state: FSMContext):
    await state.update_data(delivery_photo=message.photo[-1].file_id)
    await state.set_state(DeliveryState.waiting_for_video)
    await message.answer("🎥 <b>3-qadam:</b> Video yuboring.", parse_mode="HTML")

@router.message(DeliveryState.waiting_for_video, F.video_note)
async def process_delivery_video(message: Message, state: FSMContext):
    await state.update_data(delivery_video=message.video_note.file_id)
    data = await state.get_data()
    await state.set_state(None)
    await message.answer("✅ Tekshirib tasdiqlang:", reply_markup=ReplyKeyboardRemove())
    
    preview_caption = f"🏢 <b>Obyekt:</b> {data.get('current_obj_name')}\n📦 <b>Matn:</b>\n{data.get('delivery_text')}"
    await message.answer_photo(photo=data.get("delivery_photo"), caption=preview_caption, parse_mode="HTML")
    await message.answer_video_note(video_note=data.get("delivery_video"), reply_markup=get_confirm_delivery_keyboard())

@router.callback_query(F.data == "confirm_delivery")
async def confirm_delivery_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    msg = await callback.message.answer("⏳ Saqlanmoqda...")
    data = await state.get_data()
    emp_id = data.get("emp_id", "Noma'lum")
    delivery_text = data.get('delivery_text')
    
    try:
        group_caption = f"🏢 <b>Obyekt:</b> {data.get('current_obj_name')}\n👤 <b>Logist:</b> {emp_id}\n\n📦 <b>Matn:</b>\n{delivery_text}"
        msg_photo = await callback.bot.send_photo(
            chat_id=LOGIST_GROUP_ID, photo=data.get("delivery_photo"), caption=group_caption[:1024], parse_mode="HTML"
        )
        msg_vid = await callback.bot.send_video_note(chat_id=LOGIST_GROUP_ID, video_note=data.get("delivery_video"))
        
        await asyncio.to_thread(
            repo.save_delivery_data, emp_id, str(callback.from_user.id), data.get("current_cid", ""), 
            data.get("current_oid", ""), delivery_text, str(msg_photo.message_id), 
            str(msg_vid.message_id), datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        )
        await msg.edit_text("✅ Muvaffaqiyatli saqlandi!")
    except Exception as e:
        logger.error(f"Xato: {e}")
        await msg.edit_text("❌ Guruhga yuborishda xatolik yuz berdi.")
        
    await callback.message.answer("Menyuga qaytdingiz.", reply_markup=get_object_action_reply_keyboard())
    await callback.answer()

@router.callback_query(F.data == "cancel_delivery")
async def cancel_delivery_handler(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=get_object_action_reply_keyboard())
    await callback.answer()

@router.message(F.text == "📦 Avval yetkazilganlar")
@router.message(F.text == "📦 Yetkazilgan mahsulotlar")
async def show_previous_deliveries(message: Message, state: FSMContext):
    data = await state.get_data()
    oid = data.get("current_oid")
    role = data.get("user_role")
    
    if not oid: return await message.answer("⚠️ Avval obyektni tanlang.")
        
    wait_msg = await message.answer("Arxiv o'qilmoqda... ⏳")
    deliveries, inventory = await asyncio.gather(
        asyncio.to_thread(repo.get_deliveries_by_oid, oid),
        asyncio.to_thread(repo.get_object_inventory_summary, oid) if role == "logist" else asyncio.sleep(0)
    )
    await wait_msg.delete()
    
    if deliveries:
        await message.answer("📦 <b>Oxirgi yetkazmalar:</b>", parse_mode="HTML")
        limit = 10 if role == "client" else 5
        
        for i, d in enumerate(deliveries[-limit:], 1):
            tartib = f"🔄 <b>{i}-YETKAZMA</b>\n📅 {d['date_time']}"
            if role == "logist":
                tartib += f"\n👤 <b>Mas'ul logist:</b> {d['emp_id']}"
            
            matn = d['txt_id']
            if matn.isdigit() and len(matn) < 15:
                await message.answer(tartib, parse_mode="HTML")
                for msg_id in [d['txt_id'], d['pht_id'], d['vid_id']]:
                    if msg_id.isdigit():
                        try: await message.bot.copy_message(chat_id=message.from_user.id, from_chat_id=LOGIST_GROUP_ID, message_id=int(msg_id))
                        except Exception: pass
            else:
                caption = f"{tartib}\n\n📦 <b>Matn:</b>\n{matn}"
                if len(caption) > 1024: caption = caption[:1020] + "..."
                if d['pht_id'].isdigit():
                    try:
                        await message.bot.copy_message(
                            chat_id=message.from_user.id, from_chat_id=LOGIST_GROUP_ID, message_id=int(d['pht_id']), caption=caption, parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Rasm nusxalashda xato: {e}")
                if d['vid_id'].isdigit():
                    try: await message.bot.copy_message(chat_id=message.from_user.id, from_chat_id=LOGIST_GROUP_ID, message_id=int(d['vid_id']))
                    except Exception: pass
            await asyncio.sleep(0.5)
            
    if role == "logist" and inventory:
        summary_text = f"📊 <b>MAHSULOTLAR BALANSI:</b>\n\n"
        count = 1
        for mahsulot, hajmlar in inventory.items():
            if round(hajmlar['soni'], 2) > 0 or round(hajmlar['kvm'], 2) > 0:
                s_str = f"{hajmlar['soni']:g} dona" if hajmlar['soni'] > 0 else ""
                k_str = f"{hajmlar['kvm']:g} kv.m" if hajmlar['kvm'] > 0 else ""
                summary_text += f"<b>{count}. {mahsulot}</b> — <i>{' / '.join(filter(None, [s_str, k_str]))}</i>\n"
                count += 1
        if count == 1: summary_text += "Barcha mahsulotlar nolga teng."
        await message.answer(summary_text, parse_mode="HTML")
    
    if not deliveries:
        await message.answer("🤷‍♂️ Bu obyekt bo'yicha hali rasm yoki videoli yetkazish tarixi mavjud emas.")

@router.message(F.text == "📊 Obyekt hisoboti")
async def client_object_report(message: Message, state: FSMContext):
    data = await state.get_data()
    oid = data.get("current_oid")
    if not oid:
        return await message.answer("Iltimos, avval obyektni tanlang.")
    
    wait_msg = await message.answer("Hisobot tayyorlanmoqda... ⏳")
    project = repo.get_object_by_oid(oid)
    inventory = repo.get_object_inventory_summary(oid)
    await wait_msg.delete()
    
    if not project:
        return await message.answer("❌ Obyekt ma'lumotlari topilmadi.")

    alukabond_inventory = {}
    total_soni = 0.0
    total_kvm = 0.0
    
    if inventory:
        for mahsulot, hajmlar in inventory.items():
            turi = hajmlar.get('turi', '').lower()
            m_lower = mahsulot.lower()
            if 'aluk' in turi or 'alyuk' in turi or 'aluk' in m_lower or 'alyuk' in m_lower or 'bond' in m_lower:
                if round(hajmlar['soni'], 2) > 0 or round(hajmlar['kvm'], 2) > 0:
                    alukabond_inventory[mahsulot] = hajmlar
                    total_soni += hajmlar['soni']
                    total_kvm += hajmlar['kvm']
    
    total_soni_str = f"{total_soni:g} dona" if total_soni > 0 else ""
    total_kvm_str = f"{total_kvm:g} kv.m" if total_kvm > 0 else ""
    total_str = " / ".join(filter(None, [total_soni_str, total_kvm_str])) or "0 dona"

    report_text = f"🏢 <b>Obyekt:</b> {project.name}\n"
    report_text += f"📊 <b>Umumiy yetkazilgan Alukabond:</b> {total_str}\n\n"
    
    if alukabond_inventory:
        report_text += f"<b>Turlari bo'yicha:</b>\n"
        count = 1
        for mahsulot, hajmlar in alukabond_inventory.items():
            s_str = f"{hajmlar['soni']:g} dona" if hajmlar['soni'] > 0 else ""
            k_str = f"{hajmlar['kvm']:g} kv.m" if hajmlar['kvm'] > 0 else ""
            h_info = " / ".join(filter(None, [s_str, k_str]))
            
            report_text += f"<b>{count}.</b> {mahsulot} — <i>{h_info}</i>\n"
            count += 1
    else:
        report_text += "Hozirda obyektga alukabond yetkazilmagan."

    await message.answer(report_text, parse_mode="HTML", reply_markup=get_client_object_action_reply_keyboard())


@router.callback_query(F.data.startswith("wake_"))
async def handle_wake_response(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    if len(parts) < 3: return
    
    answer = parts[1]
    time_str = parts[2]
    name = callback.from_user.full_name
        
    if answer == "yes":
        
        await state.update_data(wake_time=time_str, wake_name=name)
        await state.set_state(WakeState.waiting_for_report)
        
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n<b>Sizning javobingiz:</b> ✅ HA\n\n✍️ <i>Iltimos, kirim yoki chiqim haqida batafsil ma'lumot (hisobot) yozib yuboring:</i>", 
            parse_mode="HTML"
        )
        await callback.answer()
        
    else:

        user_reply_text = "❌ YO'Q (Hech narsa yo'q)"
        await callback.message.edit_text(f"{callback.message.html_text}\n\n<b>Sizning javobingiz:</b> {user_reply_text}", parse_mode="HTML")
        
        admin_ids = await asyncio.to_thread(repo.get_all_admins_tg_ids)
        report_text = (
            f"📩 <b>WAKE HISOBOTI:</b>\n\n"
            f"👤 <b>Xodim:</b> {name}\n"
            f"⏰ <b>So'rov vaqti:</b> {time_str}\n"
            f"💬 <b>Javobi:</b> {user_reply_text}"
        )
        for adm in admin_ids:
            try: await callback.bot.send_message(chat_id=adm, text=report_text, parse_mode="HTML")
            except Exception: pass
                
        await callback.answer("Javobingiz adminga yuborildi. Rahmat!", show_alert=True)

@router.message(WakeState.waiting_for_report, F.text)
async def process_wake_report(message: Message, state: FSMContext):
    data = await state.get_data()
    time_str = data.get("wake_time", "Noma'lum")
    name = data.get("wake_name", message.from_user.full_name)
    report_msg = message.text
    
    admin_ids = await asyncio.to_thread(repo.get_all_admins_tg_ids)
    report_text = (
        f"📩 <b>WAKE BATAFSIL HISOBOTI:</b>\n\n"
        f"👤 <b>Xodim:</b> {name}\n"
        f"⏰ <b>So'rov vaqti:</b> {time_str}\n"
        f"💬 <b>Javobi:</b> ✅ HA (Kirim/Chiqim mavjud)\n\n"
        f"📝 <b>Izoh:</b>\n{report_msg}"
    )
    
    for adm in admin_ids:
        try: await message.bot.send_message(chat_id=adm, text=report_text, parse_mode="HTML")
        except Exception as e: logger.error(f"Failed sending wake to admin: {e}")

    await message.answer(
        "✅ Batafsil hisobotingiz qabul qilindi va adminga yuborildi.\n\n"
        "Yana boshqa ma'lumot (kirim/chiqim) kiritasizmi?", 
        reply_markup=get_wake_more_keyboard()
    )

@router.callback_query(F.data == "wake_more_yes")
async def wake_more_yes_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✍️ <i>Iltimos, keyingi hisobotni yozib yuboring (Text shaklida):</i>", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "wake_more_no")
async def wake_more_no_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Barcha hisobotlaringiz uchun rahmat!")
    await callback.answer()

@router.message()
async def select_object_by_clean_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("user_role")
    
    if role == "logist":
        obj_map = data.get("logist_objects_map", {})
        if message.text in obj_map:
            oid = obj_map[message.text]
            wait_msg = await message.answer("Olinmoqda... ⏳")
            project = await asyncio.to_thread(repo.get_object_by_oid, oid)
            await wait_msg.delete()
            
            if project:
                if project.ustalar:
                    ustalar_str = "\n" + "\n".join([f"  ▫️ {u}" for u in project.ustalar])
                else:
                    ustalar_str = " Kiritilmagan"
                
                await state.update_data(current_oid=oid, current_obj_name=project.name, current_cid=project.cid)
                
                text = (
                    f"🏢 <b>Nomi:</b> {project.name}\n"
                    f"👤 <b>Mijoz:</b> {project.client_name}\n"
                    f"📍 <b>Hudud:</b> {project.hudud}\n"
                    f"📅 <b>Boshlanish sanasi:</b> {project.start_date}\n"
                    f"📊 <b>Status:</b> {project.status}\n\n"
                    f"💰 <b>Summa:</b> {project.format_money(project.yakuniy_summa)}\n"
                    f"💵 <b>To'landi:</b> {project.format_money(project.tolandi)}\n"
                    f"📉 <b>Qarzdorlik:</b> {project.format_money(project.qarzdorlik)}\n\n"
                    f"👷‍♂️ <b>Brigadir:</b> {project.brigadir}\n"
                    f"🛠 <b>Ustalar:</b>{ustalar_str}\n\n"
                    f"<i>Qanday amal bajaramiz?</i>"
                )
                await message.answer(text, parse_mode="HTML", reply_markup=get_object_action_reply_keyboard())
            else:
                await message.answer("❌ Ma'lumot topilmadi.", reply_markup=get_logist_main_menu())
            return
            
    elif role == "client":
        obj_map = data.get("client_objects_map", {})
        if message.text in obj_map:
            oid = obj_map[message.text]
            await state.update_data(current_oid=oid, current_obj_name=message.text)
            
            await message.answer(
                f"🏢 <b>{message.text}</b> tanlandi.\nQuyidagi menyudan kerakli bo'limni tanlang:", 
                parse_mode="HTML", 
                reply_markup=get_client_object_action_reply_keyboard()
            )
            return