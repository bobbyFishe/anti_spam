import logging

from aiogram.types import Message

async def echo_handler(message: Message) -> None:
    """Эхо-функция для тестов (можно вызвать вручную, если нужно)."""
    try:
        chat_id = message.chat.id
        chat_title = message.chat.title or "Личный чат"
        chat_type = message.chat.type
        
        await message.answer(
            f"Эхо вашего сообщения:\n"
            f"<b>{message.text}</b>\n\n"
            f"Информация о чате:\n"
            f"• ID чата: <code>{chat_id}</code>\n"
            f"• Название: {chat_title}\n"
            f"• Тип: {chat_type}"
        )
    except Exception as e:
        logging.error(f"Ошибка в echo: {e}")
        await message.answer("Произошла ошибка при эхо 😔")