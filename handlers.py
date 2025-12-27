import random
import logging
import asyncio
from datetime import timedelta

from aiogram import Bot
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode, ChatMemberStatus

from config import MUTED_PERMISSIONS, FULL_PERMISSIONS, captcha_tasks, filter_list_name, ADMIN_ID, TIME_SECONDS_BAN, recent_messages, TIME_FOR_ANSWER
from utils import echo_handler

async def on_new_member(update: ChatMemberUpdated, bot: Bot):
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
    c = random.randint(1, 10)
    correct = a + b * c

    options = [correct]
    while len(options) < 6:
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

    # Отправляем начальное сообщение
    sent_message = await bot.send_message(
        chat_id=chat_id,
        text=f"👋 Привет, {user.mention_html()}!\n\n"
             f"Решите пример:\n<b>{a} + {b} × {c} = ?</b>\n\n"
             f"⏳ У тебя <b>{TIME_FOR_ANSWER}</b> секунд...",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

    # Сохраняем данные для таймера
    captcha_tasks[user.id] = {
        "chat_id": chat_id,
        "correct": correct,
        "message_id": sent_message.message_id,
        "user_mention": user.mention_html(),
        "a": a, "b": b, "c": c,
        "keyboard": keyboard,
        "task": None  # Будет хранить задачу таймера
    }
    
    # Запускаем таймаут и секундный отсчёт
    asyncio.create_task(captcha_timeout(user.id, chat_id, sent_message.message_id, bot))
    asyncio.create_task(update_captcha_timer(user.id, chat_id, sent_message.message_id, bot))


async def update_captcha_timer(user_id: int, chat_id: int, message_id: int, bot: Bot):
    """Умный таймер с разной частотой обновления"""
    try:
        for remaining in range(TIME_FOR_ANSWER, 0, -1):
            await asyncio.sleep(1)
            
            if user_id not in captcha_tasks:
                return
            
            # Определяем, нужно ли обновлять
            should_update = False
            
            if remaining <= 4:
                # Последние 4 секунды - каждую секунду
                should_update = True
            elif remaining <= 10:
                # С 5 по 10 секунду - каждую 2 секунду
                if remaining % 2 == 0:  # 10, 8, 6
                    should_update = True
            elif remaining <= 20:
                # С 11 по 20 секунду - каждые 5 секунд
                if remaining % 5 == 0:  # 20, 15, 10 (но 10 уже обработано выше)
                    should_update = True
            # else:
            #     # Свыше 20 секунд - каждые 10 секунд
            #     if remaining % 10 == 0:  # 30, 20 (но 20 уже обработано выше)
            #         should_update = True
            
            if should_update:
                task_data = captcha_tasks[user_id]
                
                # Создаём простой прогресс-бар
                progress = int((remaining / TIME_FOR_ANSWER) * 10)
                bar = "🟩" * progress + "⬜" * (10 - progress)

                if remaining > 10:
                    icon = "⏳"
                elif remaining > 5:
                    icon = "⚠️"
                else:
                    icon = "🔴"
                
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"👋 Привет, {task_data['user_mention']}!\n\n"
                             f"Решите пример:\n<b>{task_data['a']} + {task_data['b']} × {task_data['c']} = ?</b>\n\n"
                             f"{icon} {bar}\n"
                             f"Осталось: <b>{remaining}</b> сек",
                        parse_mode=ParseMode.HTML,
                        reply_markup=task_data["keyboard"]
                    )
                except Exception as e:
                    if "message to edit not found" not in str(e):
                        logging.error(f"Ошибка обновления: {e}")
                    break
                    
    except Exception as e:
        logging.error(f"Ошибка в таймере: {e}")


async def captcha_timeout(user_id: int, chat_id: int, message_id: int, bot: Bot):
    """Таймаут CAPTCHA (кик пользователя)"""
    await asyncio.sleep(TIME_FOR_ANSWER + 2) # +2 чтобы не было рассинхрона с отчетом
    if user_id in captcha_tasks:
        try:
            await bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=timedelta(seconds=1)
            )
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)

            await bot.delete_message(chat_id=chat_id, message_id=message_id)

            await bot.send_message(
                chat_id=chat_id,
                text=f"⏰ Пользователь <a href='tg://user?id={user_id}'>[ID {user_id}]</a> не прошёл CAPTCHA за {TIME_FOR_ANSWER} секунд — выкинут из группы."
            )
        except Exception as e:
            logging.error(f"Ошибка при таймауте CAPTCHA: {e}")

        captcha_tasks.pop(user_id, None)


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

    if answer == correct:
        # Правильно — снимаем мут
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=FULL_PERMISSIONS
        )
        # Удаляем сообщение с таймером
        await callback.message.delete()
        
        await bot.send_message(
            chat_id=chat_id,
            text=f"✅ {callback.from_user.mention_html()} прошёл проверку и теперь может писать!"
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

    # Удаляем задачу (остановит таймер)
    if user_id in captcha_tasks:
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
    
        # === ДЕТЕКЦИЯ МАССОВЫХ ДУБЛИКАТОВ ===
    text_clean = " ".join(message.text.lower().split())  # Убираем лишние пробелы, приводим к нижнему регистру

    # Очищаем список от старых (если > MAX_RECENT = 30 например)
    if len(recent_messages) > 30:
        recent_messages.pop(0)

    # Проверяем повтор от одного пользователя
    if recent_messages and recent_messages[-1][0] == text_clean and recent_messages[-1][1] == message.from_user.id:
        # Повтор от того же человека — бан только его
        await ban_user_for_spam(message, bot, "повторение одного и того же сообщения")
        return

    # Считаем, сколько раз это сообщение уже было
    duplicates = [m for m in recent_messages if m[0] == text_clean]

    # Если уже было 2 или больше — это массовый спам
    if len(duplicates) >= 2:
        # Баним ВСЕХ, кто отправлял этот текст (включая текущего)
        banned_users = set()
        for _, user_id in duplicates:
            try:
                member = await bot.get_chat_member(message.chat.id, user_id)
                if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                    continue
            except Exception:
                pass
            if user_id not in banned_users:
                try:
                    await bot.ban_chat_member(
                        chat_id=message.chat.id,
                        user_id=user_id,
                        until_date=timedelta(seconds=TIME_SECONDS_BAN)  # или TIME_SECONDS_BAN
                    )
                    banned_users.add(user_id)
                except Exception as e:
                    logging.error(f"Не удалось забанить {user_id}: {e}")

        # Баним и текущего отправителя
        await ban_user_for_spam(message, bot, "массовый спам одинаковым сообщением")

        # Уведомление
        await bot.send_message(
            message.chat.id,
            f"🚫 Обнаружен массовый спам одинаковым сообщением — забанены все отправители."
        )
        return

    # Сохраняем новое сообщение

    # Перед добавлением сообщения в историю
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]

    if not is_admin:
        recent_messages.append((text_clean, message.from_user.id))
    # === КОНЕЦ ДЕТЕКЦИИ ===


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

async def ban_user_for_spam(message: Message, bot: Bot, reason: str):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    
    if is_admin:
        await message.reply(f"Админ {message.from_user.first_name}, осторожнее! Вы спамите.")
        return
    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            until_date=timedelta(seconds=TIME_SECONDS_BAN)
        )
        await message.delete()

        user_mention = f"@{message.from_user.username}" if message.from_user.username else f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"

        await bot.send_message(
            message.chat.id,
            f"🚫 Пользователь {user_mention} забанен за {reason}.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Ошибка бана: {e}")