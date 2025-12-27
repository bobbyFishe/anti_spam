from aiogram.types import ChatPermissions
import random

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

CAPTCHA_TASKS = [
    # Математические
    {
        "type": "math",
        "generate": lambda: {
            "a": random.randint(1, 10),
            "b": random.randint(1, 10),
            "operation": random.choice(["+", "-", "*"]),
        },
        "solve": lambda task: {
            "+": task["a"] + task["b"],
            "-": task["a"] - task["b"],
            "*": task["a"] * task["b"],
        }[task["operation"]],
        "format": lambda task: f"{task['a']} {task['operation']} {task['b']} = ?",
    },
    # Словарные
    {
        "type": "word_count",
        "generate": lambda: {
            "word": random.choice(["привет", "телеграм", "бот", "капча", "защита"]),
        },
        "solve": lambda task: len(task["word"]),
        "format": lambda task: f"Сколько букв в слове '{task['word'].upper()}'?",
    },
    # Логические
    {
        "type": "logic",
        "generate": lambda: {
            "question": random.choice([
                {"q": "Фигура с 3 углами?", "a": "треугольник"},
                {"q": "RGB(255,0,0) - цвет?", "a": "красный"},
                {"q": "Столица России?", "a": "москва"},
                {"q": "2+2*2?", "a": "6"},
                {"q": "Нечетное число?", "a": random.choice(["1", "3", "5", "7", "9"])},
            ])
        },
        "solve": lambda task: task["question"]["a"],
        "format": lambda task: task["question"]["q"],
    },
    # Простые вопросы
    {
        "type": "simple",
        "generate": lambda: {
            "question": random.choice([
                {"q": "Сколько дней в неделе?", "a": "7"},
                {"q": "Сколько часов в сутках?", "a": "24"},
                {"q": "Первая буква алфавита?", "a": "а"},
                {"q": "Сколько пальцев на руке?", "a": "5"},
                {"q": "Какой сейчас век? (римскими)", "a": "xxi"},
            ])
        },
        "solve": lambda task: task["question"]["a"],
        "format": lambda task: task["question"]["q"],
    },
    # Последовательности
    {
        "type": "sequence",
        "generate": lambda: {
            "sequence": random.choice([
                {"seq": "2, 4, 6, ?", "a": "8"},
                {"seq": "1, 3, 5, ?", "a": "7"},
                {"seq": "А, Б, В, ?", "a": "г"},
                {"seq": "5, 10, 15, ?", "a": "20"},
                {"seq": "Январь, Февраль, ?", "a": "март"},
            ])
        },
        "solve": lambda task: task["sequence"]["a"],
        "format": lambda task: f"Продолжи последовательность: {task['sequence']['seq']}",
    },
]

TIME_FOR_ANSWER = 20
captcha_tasks = {}

filter_list_name = {"пароль", "логин", "аккаунт", "карта", "счет", "перевод",
    "кликни", "ссылка", "бесплатный", "выиграл", "приз", "розыгрыш",
    "подарок", "срочно", "секрет", "обман", "развод", "халява", "дурак", "идиот", "дебил", "тупой", "кретин", "ублюдок",
    "сволочь", "мудак", "пидор", "педик", "гей", "лох", "чмо",
    "сука", "бля", "хуй", "пизд", "ебать", "ебан", "похер", "порно", "секс", "голый", "обнажен", "интим", "трах",
    "сосет", "лижет", "оргия", "изнасилование", "педофил", "наркотик", "героин", "кокаин", "марихуана", "гашиш",
    "спайс", "мефедрон", "лсд" }  # Запрещённые слова

ADMIN_ID = 867705312  # Твой ID

TIME_SECONDS_BAN = 30  # Время бана в секундах

recent_messages = []  # Список последних сообщений: (text_clean, user_id)
MAX_RECENT = 20       # Храним последние 20 сообщений