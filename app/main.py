import logging
import os
import requests
import telebot
from dotenv import load_dotenv
import constants
from dbconnector import DBConnector
from user import User
from user import get_base
from sqlalchemy import update, select, exc
import schedule
from time import sleep
from threading import Thread
from datetime import datetime, time as get_time

load_dotenv()


def initialize_telebot():
    bot_token = os.getenv('BOT_TOKEN')
    t_bot = telebot.TeleBot(bot_token)
    return t_bot


logger = None
mysql_connection = None
bot = initialize_telebot()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_info = {
        "user_id": message.from_user.id,
        "chat_id": message.chat.id,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name
    }
    register_new_user(user_info)
    bot.reply_to(message, constants.WELCOME_TEXT)
    bot.send_message(message.chat.id, constants.POEM_CHOICE_TEXT)


def get_random_poem(poet_id):
    response = requests.get(f"{constants.GANJOOR_API_URL}/api/ganjoor/poem/random", params={"poetId": poet_id})
    if response.status_code == 200:
        logger.info("Sent poem.")
        return response.json()
    logger.error("Failed to get random poem")
    return ""


def send_poem_to_user(user_id, poet_id):
    poem_dict = get_random_poem(poet_id)
    poem_text = poem_dict["plainText"]
    poem_title = poem_dict["fullTitle"]
    bot.send_message(user_id, f"{poem_text}\n\n*{poem_title}*", parse_mode='Markdown')


@bot.message_handler(commands=["send_now"])
def send_poem_now(message):
    user_fav_poet = get_user_favorite_poet(message.from_user.id)
    send_poem_to_user(message.chat.id, user_fav_poet)


def get_user_favorite_poet(user_id):
    stmt = select(User.favorite_poet).where(User.id == user_id)
    result = mysql_connection.session.execute(stmt)
    r = [x for x in result]
    logger.info(f"this is the result {r[0][0]}")
    return r[0][0]


@bot.message_handler(regexp=r"(1|2|3|7)")
def set_favorite_poet(message):
    user_id = message.from_user.id
    response = message.text
    logger.info(f"we got {response} from a user")
    set_favorite_poet_in_db(user_id, response)
    bot.send_message(message.chat.id, constants.CHOOSE_SUCCEEDED)


def register_new_user(user_info):
    user = User(**user_info)
    try:
        mysql_connection.session.add(user)
        mysql_connection.session.commit()
        logger.info("New user registered")
    except exc.IntegrityError:
        mysql_connection.session.rollback()
        logger.info("user already exits")


def set_favorite_poet_in_db(user_id, poet_number):
    stmt = update(User).where(User.user_id == user_id).values(favorite_poet=poet_number)
    mysql_connection.session.execute(stmt)
    mysql_connection.session.commit()
    logger.info("updated user favorite poet")


def send_poem_to_all_users():
    all_users = mysql_connection.session.query(User).all()
    for user in all_users:
        send_poem_to_user(user.chat_id, user.favorite_poet)


def establish_db_connection():
    connector = DBConnector(host=os.getenv("MYSQL_HOST"),
                            user=os.getenv("MYSQL_USER"),
                            password=os.getenv("MYSQL_PASSWORD"),
                            database=os.getenv("MYSQL_DB")
                            )
    logger.info("connected to mysql")
    connector.create_session()
    base = get_base()
    base.metadata.create_all(connector.engine)
    logger.info("created all schemas")
    return connector


def initialize_logger():
    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


def run_scheduler():
    scheduled_time = get_time(hour=18, minute=0, second=0)
    scheduled_time = get_time(hour=20, minute=48, second=0)
    schedule.every().day.at(str(scheduled_time)).do(send_poem_to_all_users)

    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    logger = initialize_logger()
    mysql_connection = establish_db_connection()
    Thread(target=run_scheduler).start()
    bot.infinity_polling()
