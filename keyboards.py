from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_public_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ℹ️ Biz haqimizda"), KeyboardButton(text="📍 Manzil va Aloqa")],
            [KeyboardButton(text="💼 Bo'sh ish o'rinlari"), KeyboardButton(text="🤝 Mijozlar bo'limi")]
        ],
        resize_keyboard=True
    )

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Telefon raqam yuborish", request_contact=True)]], 
        resize_keyboard=True, 
        one_time_keyboard=True
    )

def get_logist_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Obyektlar")],
            [KeyboardButton(text="🚪 Tizimdan chiqish")]
        ],
        resize_keyboard=True
    )

def get_objects_reply_keyboard(objects_list: list) -> ReplyKeyboardMarkup:
    buttons = []
    for i in range(0, len(objects_list), 2):
        row = [KeyboardButton(text=f"{obj.name} ({obj.client_name})") for obj in objects_list[i:i+2]]
        buttons.append(row)
    buttons.append([KeyboardButton(text="🔙 Asosiy menyu")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_object_action_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Mahsulot yetkazildi"), KeyboardButton(text="📦 Avval yetkazilganlar")],
            [KeyboardButton(text="🔙 Obyektlar ro'yxatiga")]
        ],
        resize_keyboard=True
    )

def get_cancel_process_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]],
        resize_keyboard=True
    )

def get_confirm_delivery_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlayman", callback_data="confirm_delivery"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_delivery")
            ]
        ]
    )

def get_client_objects_reply_keyboard(objects_list: list) -> ReplyKeyboardMarkup:
    buttons = []
    for i in range(0, len(objects_list), 2):
        row = [KeyboardButton(text=f"{obj.name}") for obj in objects_list[i:i+2]]
        buttons.append(row)

    buttons.append([KeyboardButton(text="🚪 Tizimdan chiqish")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_client_object_action_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Obyekt hisoboti"), KeyboardButton(text="📦 Yetkazilgan mahsulotlar")],
            [KeyboardButton(text="🔙 Obyektlar ro'yxatiga")]
        ],
        resize_keyboard=True
    )

def get_admin_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Yangilash")],
            [KeyboardButton(text="🚪 Tizimdan chiqish")]
        ],
        resize_keyboard=True
    )

def get_wake_confirm_keyboard(time_str: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha (Bor)", callback_data=f"wake_yes_{time_str}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"wake_no_{time_str}")
            ]
        ]
    )

def get_wake_more_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yana qo'shish", callback_data="wake_more_yes"),
                InlineKeyboardButton(text="✅ Yakunlash", callback_data="wake_more_no")
            ]
        ]
    )