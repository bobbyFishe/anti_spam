import random
import logging
import asyncio
from datetime import timedelta

from aiogram import Bot
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode, ChatMemberStatus

from config import MUTED_PERMISSIONS, FULL_PERMISSIONS, captcha_tasks, filter_list_name, ADMIN_ID, TIME_SECONDS_BAN
from utils import echo_handler

# Новый обработчик присоединения с CAPTCHA в группе
async def on_new_member(update: ChatMemberUpdated, bot: Bot):
    # logging.info(f"Получено событие chat_member: old={update.old_chat_member.status} -> new={update.new_chat_member.status}, user={update.new_chat_member.user.id}")
    # if update.new_chat_member.status == "member":
    #     user = update.new_chat_member.user
    #     chat_id = update.chat.id

    #     await bot.send_message(chat_id, f"Тест: {user.full_name} теперь member!")
    
    
    
    if update.new_chat_member.status != "member":
        return
    if update.old_chat_member.status not in ["left", "kicked", None]:
        return

    user = update.new_chat_member.user
    chat_id = update.chat.id

    if user.is_bot:
        return

    if user.id in captcha_tasks:
        del captcha_tasks[user.id]

    a = random.randint(1, 10)
    b = random.randint(1, 10)
    correct = a + b

    options = [correct]
    while len(options) < 4:
        wrong = correct + random.randint(-8, 8)
        if wrong <= 0 or wrong in options:
            continue
        options.append(wrong)
    random.shuffle(options)

    # Создаём клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for opt in options:
        row.append(InlineKeyboardButton(
            text=str(opt),
            callback_data=f"captcha:{opt}:{correct}:{user.id}:{chat_id}"
        ))
        if len(row) == 2:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    # Мутируем пользователя
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user.id,
        permissions=MUTED_PERMISSIONS
    )

    sent_message = await bot.send_message(
        chat_id=chat_id,
        text=f"👋 Привет, {user.mention_html()}!\n\n"
             f"Чтобы получить право писать, решите простой пример:\n\n"
             f"<b>{a} + {b} = ?</b>\n\n"
             f"Нажмите на правильный ответ:",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

    captcha_tasks[user.id] = {
        "chat_id": chat_id,
        "correct": correct,
        "message_id": sent_message.message_id
    }

    asyncio.create_task(captcha_timeout(user.id, chat_id, sent_message.message_id, bot))

async def captcha_timeout(user_id: int, chat_id: int, message_id: int, bot: Bot):
    await asyncio.sleep(30)  # 30 секунд на ответ

    if user_id in captcha_tasks:
        try:
            # Выкидываем из группы (kick — может вернуться сразу)
            await bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=timedelta(seconds=1)  # Минимальный бан для кика
            )
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)  # Сразу разбаниваем — чистый kick

            # Удаляем сообщение с CAPTCHA
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

            # Уведомление в группу
            await bot.send_message(
                chat_id=chat_id,
                text=f"⏰ Пользователь <a href='tg://user?id={user_id}'>[ID {user_id}]</a> не прошёл CAPTCHA за 30 секунд — выкинут из группы."
            )
        except Exception as e:
            logging.error(f"Ошибка при таймауте CAPTCHA: {e}")

        # Очищаем задачу
        captcha_tasks.pop(user_id, None)

# Новый обработчик нажатия на кнопку
async def captcha_callback(callback: CallbackQuery, bot: Bot):
    if not callback.data.startswith("captcha:"):
        return

    data = callback.data.split(":")
    answer = int(data[1])
    correct = int(data[2])
    user_id = int(data[3])
    chat_id = int(data[4])

    # Проверяем, что это тот же пользователь
    if callback.from_user.id != user_id:
        await callback.answer("Это не ваша CAPTCHA!", show_alert=True)
        return

    if user_id not in captcha_tasks:
        await callback.answer("CAPTCHA истекла или уже пройдена.", show_alert=True)
        return

    task = captcha_tasks[user_id]

    if answer == correct:
        # Правильно — снимаем мут
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=FULL_PERMISSIONS
        )
        await callback.message.edit_text(
            f"✅ {callback.from_user.mention_html()} прошёл проверку и теперь может писать!"
        )
    else:
        try:
            await bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=timedelta(seconds=TIME_SECONDS_BAN)
            )
            # Удаляем сообщение с CAPTCHA
            await callback.message.delete()

            user_mention = f"@{callback.from_user.username}" if callback.from_user.username else f"<a href='tg://user?id={user_id}'>{callback.from_user.first_name}</a>"

            await bot.send_message(
                chat_id=chat_id,
                text=f"🚫 Пользователь {user_mention} дал неправильный ответ на CAPTCHA и забанен на {TIME_SECONDS_BAN} секунд."
            )
        except Exception as e:
            logging.error(f"Ошибка при бане за неправильную CAPTCHA: {e}")
            await callback.message.edit_text("Ошибка при обработке ответа.")

        await callback.answer("❌ Неверно!", show_alert=True)

    # Удаляем задачу
    captcha_tasks.pop(user_id, None)
    await callback.answer()

# Остальные обработчики (без изменений, кроме удаления старого check_captcha и on_new_member)
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {message.from_user.full_name}!")

async def help_handler(message: Message) -> None:
    await message.answer("Я — бот-помощник. Команды: /start, /help")

async def add_word(message: Message):
    if message.text is None:
        await message.reply("Использование: /addword <слово>")
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Укажите слово после команды: /addword <слово>", parse_mode=None)
        return
    new_words = parts[1:]
    if message.from_user.id == ADMIN_ID:
        added_count = 0
        for spam in new_words:
            spam = spam.lower().strip()
            if spam and spam not in filter_list_name:
                filter_list_name.add(spam)
                added_count += 1
        if added_count > 0:
            await message.reply(f"Добавлено {added_count} слов(а): {', '.join(new_words)}")
        else:
            await message.reply("Новых слов не добавлено (возможно, дубликаты)")
    else:
        await message.reply("У вас нет прав")

async def filter_handler(message: Message, bot: Bot):
    if not message.text:
        return

    text_lower = message.text.lower()
    detected_word = None
    for spam in filter_list_name:
        if spam in text_lower:
            detected_word = spam
            break

    if detected_word:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]

        if is_admin:
            await message.reply(f"Админ {message.from_user.first_name}, осторожнее! Слово '{detected_word}' запрещено.")
            return

        try:
            await bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                until_date=timedelta(seconds=TIME_SECONDS_BAN)
            )
            await message.delete()

            user = message.from_user
            user_mention = f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

            await bot.send_message(
                chat_id=message.chat.id,
                text=f"🚫 Пользователь {user_mention} забанен на {TIME_SECONDS_BAN} секунд за слово: \"{detected_word}\"",
                parse_mode=ParseMode.HTML if not user.username else None
            )
        except Exception as e:
            logging.error(f"Ошибка при бане: {e}")
            await bot.send_message(message.chat.id, "Не удалось забанить пользователя")

        return

    # Эхо на нормальные сообщения (можно убрать)
    # await echo_handler(message)