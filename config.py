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

captcha_tasks = {}  # Словарь для задач CAPTCHA: user_id -> dict с задачей

filter_list_name = {"лес", "оно"}  # Запрещённые слова

ADMIN_ID = 867705312  # Твой ID

TIME_SECONDS_BAN = 30  # Время бана в секундах