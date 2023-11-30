from dotenv import load_dotenv
import os
import telebot
import sqlite3 as sql
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

load_dotenv()

token = os.getenv("TOKEN")
bot = telebot.TeleBot(token)

creation_data = {}


def check_if_in_geocaches(code):
    try:
        con = sql.connect("geocaches.db")
        cur = con.cursor()

        data = cur.execute(
            f"""SELECT * FROM geocaches WHERE website_code = '{code}'"""
        ).fetchall()

        cur.close()

        if len(data) == 1:
            return True
        return False

    except sql.Error as error:
        print("Failed to check data in sqlite table (geocaches)", error)


def check_if_on_confirmation(code):
    try:
        con = sql.connect("geocaches.db")
        cur = con.cursor()

        data = cur.execute(
            f"""SELECT * FROM on_confirmation WHERE website_code = '{code}'"""
        ).fetchall()

        cur.close()

        if len(data) == 1:
            return True
        return False

    except sql.Error as error:
        print("Failed to check data in sqlite table (on_confirmation)", error)


def delete_from_on_confirmation(code):
    try:
        con = sql.connect("geocaches.db")
        cur = con.cursor()

        deletion = f"""DELETE FROM on_confirmation WHERE website_code = '{code}'"""
        cur.execute(deletion)
        con.commit()

        cur.close()

    except sql.Error as error:
        print("Failed to delete data from sqlite table (on_confirmation)", error)


def move_to_db(code):
    try:
        con = sql.connect("geocaches.db")
        cur = con.cursor()

        data = cur.execute(
            f"""SELECT * FROM on_confirmation WHERE website_code = '{code}'"""
        ).fetchall()[0]

        insertion = """INSERT INTO geocaches
                                  (website_code, name, description, image, coordinates, questions, answers) VALUES (?, ?, ?, ?, ?, ?, ?)"""
        cur.execute(insertion, data)
        con.commit()

        delete_from_on_confirmation(code)

        cur.close()

    except sql.Error as error:
        print(
            "Failed to move data from sqlite table (on_confirmation -> geocaches)",
            error,
        )


def insert_in_db(id, name, description, image, coords, questions, answers):
    try:
        con = sql.connect("geocaches.db")
        cur = con.cursor()
        insertion = """INSERT INTO on_confirmation
                                  (website_code, name, description, image, coordinates, questions, answers) VALUES (?, ?, ?, ?, ?, ?, ?)"""

        data_tuple = (id, name, description, image, coords, questions, answers)
        cur.execute(insertion, data_tuple)
        con.commit()
        cur.close()

    except sql.Error as error:
        print("Failed to insert data into sqlite table (on_confirmation)", error)


def check_coords(c: str):
    try:
        if (
            c[0] in ["N", "S"]
            and c[1] == " "
            and c[2:4].isdigit()
            and c[4] == " "
            and c[5:7].isdigit()
            and c[7] == "."
            and c[8:11].isdigit()
            and c[11] == " "
            and c[12] in ["E", "W"]
            and c[13] == " "
            and c[14:16].isdigit()
            and c[16] == " "
            and c[17:19].isdigit()
            and c[19] == "."
            and c[20:].isdigit
            and len(c) == 23
        ):
            return True
        return False
    except Exception:
        return False


def get_parameter(text):
    try:
        return text.split()[1] if len(text.split()) > 1 else False
    except:
        return False


@bot.message_handler(commands=["start", "help"])
def start(message: Message):
    try:
        cache_code = get_parameter(message.text)
        if not cache_code:
            button_create = InlineKeyboardButton(
                "➕ Создать новый тайник", callback_data="create_cache_callbacak"
            )
            keyboard = InlineKeyboardMarkup()
            keyboard.add(button_create)
            bot.send_message(
                message.chat.id,
                "👋 Привет! Я - бот, который позволяет проходить пошаговые тайники прямо в телеграме. Кажется, ты запустил бота не по специальной ссылке. Нажав на кнопку ниже, ты можешь создать пошаговый тайник. Чтобы пройти нужный тайник, перейди по специальной ссылке этого тайника.",
                reply_markup=keyboard,
            )
        else:
            bot.send_message(message.chat.id, f"начинается квест тайника: {cache_code}")
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


@bot.callback_query_handler(func=lambda x: True)
def button_callback(call: CallbackQuery):
    try:
        data = call.data.split(";")
        match data[0]:
            case "create_cache_callbacak":
                if len(data) > 1:
                    create_cache(call.message, code=data[1])
                else:
                    create_cache(call.message)
            case "start_creation":
                creation_add_code(call.message)
            case "creation_confirmed":
                creation_successful(call.message, data[1])
            case _:
                bot.send_message(
                    call.message.chat.id,
                    "К сожалению, я не понял, что ты сделал. Пожалуйста, сообщи об этом @FoxFil.",
                )
    except Exception as e:
        bot.send_message(
            call.message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def create_cache(message: Message, code=""):
    try:
        bot.edit_message_reply_markup(
            chat_id=message.chat.id, message_id=message.message_id, reply_markup=None
        )
        if check_if_on_confirmation(code):
            delete_from_on_confirmation(code)
        button_start = InlineKeyboardButton("Начать", callback_data="start_creation")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(button_start)
        bot.send_message(
            message.chat.id,
            f"Ты в меню создания тайника. Тебе надо будет отправить мне данные твоего тайника. Я буду задавать вопросы, а тебе надо отвечать на них.",
            reply_markup=keyboard,
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_add_code(message: Message):
    try:
        bot.edit_message_reply_markup(
            chat_id=message.chat.id, message_id=message.message_id, reply_markup=None
        )
        cache_code = bot.send_message(
            message.chat.id,
            "Отправь мне код тайника в формате XX00000, где XX - буквы тайника (например, TR, VI), а 00000 - код тайника.",
        )
        bot.register_next_step_handler(cache_code, creation_add_name)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_add_name(message: Message):
    try:
        if message.text and message.text[:2].isalpha() and message.text[2:].isdigit():
            if not check_if_in_geocaches(message.text):
                data = [message.text]
                cache_name = bot.send_message(
                    message.chat.id,
                    "Отправь мне название тайника.",
                )
                bot.register_next_step_handler(
                    cache_name, creation_add_description, data
                )
            else:
                bot.send_message(
                    message.chat.id,
                    f"❌ Данный тайник уже существует. Запустить его можно по команде `/start {message.text}`",
                    parse_mode="Markdown",
                )
        else:
            cache_code = bot.send_message(
                message.chat.id,
                "❌ Неправильный формат! Отправь мне код тайника в формате XX00000, где XX - буквы тайника (например, TR, VI), а 00000 - код тайника.",
            )
            bot.register_next_step_handler(cache_code, creation_add_name)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_add_description(message: Message, data: list):
    try:
        if message.text:
            data.append(message.text)
            cache_description = bot.send_message(
                message.chat.id,
                "Отправь мне описание тайника.",
            )
            bot.register_next_step_handler(cache_description, creation_add_image, data)
        else:
            cache_code = bot.send_message(
                message.chat.id,
                "❌ Кажется, вы отправили стикер! Отправь мне название тайника.",
            )
            bot.register_next_step_handler(cache_code, creation_add_description, data)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_add_image(message: Message, data: list):
    try:
        if message.text:
            data.append(message.text)
            cache_image = bot.send_message(
                message.chat.id,
                "Отправь мне картинку тайника.",
            )
            bot.register_next_step_handler(cache_image, creation_add_coords, data)
        else:
            cache_description = bot.send_message(
                message.chat.id,
                "❌ Кажется, вы отправили стикер! Отправь мне описание тайника.",
            )
            bot.register_next_step_handler(cache_description, creation_add_image, data)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_add_coords(message: Message, data: list):
    try:
        if message.photo:
            data.append(message.photo[-1].file_id)
            cache_coords = bot.send_message(
                message.chat.id,
                """Отправь мне координаты точек тайника, перечисляя их каждый с новой строки, вот в таком формате:

`1. N 00 00.000 E 00 00.000`
`2. N 11 11.111 E 11 11.111`
`3. N 22 22.222 E 22 22.222`

⚠ ВАЖНО! Отправлять координаты, вопросы и ответы в одинаковом порядке, то есть первые координаты должны соответствовать первому вопросу и первому ответу и т.д.""",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(cache_coords, creation_add_questions, data)
        else:
            photo = bot.send_message(
                message.chat.id,
                "❌ Ты отправил мне сообщение без картинки. Пожалуйста, отправь мне картинку тайника.",
            )
            bot.register_next_step_handler(photo, creation_add_coords, data)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_add_questions(message: Message, data: list):
    try:
        OK = True
        if message.text:
            for elem in list(
                map(lambda x: " ".join(x.split()[1:]), message.text.split("\n"))
            ):
                if check_coords(elem):
                    pass
                else:
                    OK = False
        else:
            OK = False
        if OK:
            data.append(message.text)
            cache_questions = bot.send_message(
                message.chat.id,
                """Отправь мне вопросы точек тайника, перечисляя их через точку с запятой, вот в таком формате:

`1. Как дела?`
`2. Какая погода?`
`3. Что делаешь?`

⚠ ВАЖНО! Отправлять координаты, вопросы и ответы в одинаковом порядке, то есть первые координаты должны соответствовать первому вопросу и первому ответу и т.д.""",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(cache_questions, creation_add_answers, data)
        else:
            cache_coords = bot.send_message(
                message.chat.id,
                """❌ Неверный формат координат! Отправь мне координаты точек тайника, перечисляя их через точку с запятой, вот в таком формате:

`1. N 00 00.000 E 00 00.000`
`2. N 11 11.111 E 11 11.111`
`3. N 22 22.222 E 22 22.222`

⚠ ВАЖНО! Отправлять координаты, вопросы и ответы в одинаковом порядке, то есть первые координаты должны соответствовать первому вопросу и первому ответу и т.д.""",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(cache_coords, creation_add_questions, data)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_add_answers(message: Message, data: list):
    try:
        if message.text and len(
            list(map(lambda x: " ".join(x.split()[1:]), data[4].split("\n")))
        ) == len(
            list(map(lambda x: " ".join(x.split()[1:]), message.text.split("\n")))
        ):
            data.append(message.text)
            cache_answers = bot.send_message(
                message.chat.id,
                """Отправь мне ответы точек тайника, перечисляя их через точку с запятой, вот в таком формате:

`1. Хорошо`
`2. Солнечно`
`3. Гуляю`

⚠ ВАЖНО! Отправлять координаты, вопросы и ответы в одинаковом порядке, то есть первые координаты должны соответствовать первому вопросу и первому ответу и т.д.""",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(cache_answers, creation_final, data)
        else:
            cache_questions = bot.send_message(
                message.chat.id,
                f"""❌ Кажется, количество вопросов и количество координат не совпадают, либо вы отправили стикер!

Отправь мне вопросы точек тайника, перечисляя их через точку с запятой, вот в таком формате:

`1. Как дела?`
`2. Какая погода?`
`3. Что делаешь?`

⚠ ВАЖНО! Отправлять координаты, вопросы и ответы в одинаковом порядке, то есть первые координаты должны соответствовать первому вопросу и первому ответу и т.д.""",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(cache_questions, creation_add_answers, data)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_final(message: Message, data: list):
    try:
        if message.text and len(
            list(map(lambda x: " ".join(x.split()[1:]), data[5].split("\n")))
        ) == len(
            list(map(lambda x: " ".join(x.split()[1:]), message.text.split("\n")))
        ):
            data.append(message.text)

            insert_in_db(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

            coords, questions, answers = (
                list(map(lambda x: " ".join(x.split()[1:]), data[4].split("\n"))),
                list(map(lambda x: " ".join(x.split()[1:]), data[5].split("\n"))),
                list(map(lambda x: " ".join(x.split()[1:]), data[6].split("\n"))),
            )
            questions_message = ""
            for i, question in enumerate(questions):
                questions_message += (
                    f"`{i + 1}. {question} | {coords[i]} | {answers[i]}`\n"
                )

            button_confirm = InlineKeyboardButton(
                "✅", callback_data=f"creation_confirmed;{data[0]}"
            )
            button_repeat = InlineKeyboardButton(
                "🔄", callback_data=f"create_cache_callbacak;{data[0]}"
            )
            keyboard = InlineKeyboardMarkup()
            keyboard.add(button_confirm, button_repeat)

            bot.send_photo(
                message.chat.id,
                data[3],
                f"""Спасибо, что ответил на все вопросы. Вот информация о твоем тайнике.

*Код*: `{data[0]}`

*Название*: `{data[1]}`

*Описание*:

`{(data[2][:200] + '...') if len(data[2]) >= 200 else data[2]}`

*Картинка*: отправлена в приложении

*Вопросы с координатами и ответами*:

{questions_message}

Проверь всю информацию и нажми ✅, если всё верно. Если нашел ошибку, нажми 🔄 и создай тайник заново.""",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        else:
            cache_answers = bot.send_message(
                message.chat.id,
                """❌ Кажется, количество вопросов и количество ответов не совпадают!

Отправь мне ответы точек тайника, перечисляя их через точку с запятой, вот в таком формате:

`1. Хорошо`
`2. Солнечно`
`3. Гуляю`

⚠ ВАЖНО! Отправлять координаты, вопросы и ответы в одинаковом порядке, то есть первые координаты должны соответствовать первому вопросу и первому ответу и т.д.""",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(cache_answers, creation_final, data)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


def creation_successful(message: Message, code: str):
    try:
        bot.edit_message_reply_markup(
            chat_id=message.chat.id, message_id=message.message_id, reply_markup=None
        )
        move_to_db(code)
        bot.send_message(
            message.chat.id,
            f"✅ Тайник успешно создан и добавлен в базу. Спасибо!",
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⛔ Возникла ошибка, пожалуйста, сообщите об этом @FoxFil\n\nОшибка:\n\n`{e}`",
            parse_mode="Markdown",
        )


bot.infinity_polling()
