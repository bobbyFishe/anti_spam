from aiogram.types import ChatPermissions

TOKEN = "7755348011:AAGLPdrpVNtRdgTKhL7vSXxiuz37sSCLTG8"

MUTED_PERMISSIONS = ChatPermissions(can_send_messages=False)

FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
    can_pin_messages=False,
)

TIME_FOR_ANSWER = 20
captcha_tasks = {}

filter_list_name = {"пароль", "логин", "аккаунт", "карта", "счет", "перевод",
    "кликни", "ссылка", "бесплатный", "выиграл", "приз", "розыгрыш",
    "подарок", "срочно", "секрет", "обман", "развод", "халява", "дурак", "идиот", "дебил", "тупой", "кретин", "ублюдок",
    "сволочь", "мудак", "пидор", "педик", "гей", "лох", "чмо",
    "сука", "бля", "хуй", "пизда", "ебать", "ебан", "похер", "порно", "секс", "голый", "обнажен", "интим", "трах",
    "сосет", "лижет", "оргия", "изнасилование", "педофил", "наркотик", "героин", "кокаин", "марихуана", "гашиш",
    "спайс", "мефедрон", "лсд" }  # Запрещённые слова

ADMIN_ID = 867705312  # Твой ID

TIME_SECONDS_BAN = 30  # Время бана в секундах

recent_messages = []  # Список последних сообщений: (text_clean, user_id)
MAX_RECENT = 20       # Храним последние 20 сообщений