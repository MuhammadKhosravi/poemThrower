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
    poet_choosing_prompt(message)


@bot.message_handler(commands=['choose_poet'])
def poet_choosing_prompt(message):
    bot.send_message(message.chat.id, constants.POEM_CHOICE_TEXT)
    bot.register_next_step_handler(message, set_favorite_poet)


def get_random_poem(poet_id):
    if poet_id == "4":
        poet_id = "5"
    elif poet_id == "5":
        poet_id = "7"
    counter = 0
    max_retries = 3
    while counter < max_retries:
        response = requests.get(f"{constants.GANJOOR_API_URL}/api/ganjoor/poem/random", params={"poetId": poet_id})
        if response.status_code == 200:
            logger.info("Sent poem.")
            return response.json()
        counter += 1
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
    mysql_connection = get_db_connection()
    stmt = select(User.favorite_poet).where(User.user_id == user_id)
    result = mysql_connection.session.execute(stmt)
    r = [x for x in result]
    logger.info(f"this is the result {r[0][0]}")
    return r[0][0]


def set_favorite_poet(message):
    user_id = message.from_user.id
    response = message.text
    logger.info(f"we got {response} from a user")
    set_favorite_poet_in_db(user_id, response)
    bot.send_message(message.chat.id, constants.CHOOSE_SUCCEEDED)


def register_new_user(user_info):
    user = User(**user_info)
    mysql_connection = get_db_connection()
    try:
        mysql_connection.session.add(user)
        mysql_connection.session.commit()
        mysql_connection.session.close()
        logger.info("New user registered")
    except exc.IntegrityError:
        mysql_connection.session.rollback()
        logger.info("user already exits")


def set_favorite_poet_in_db(user_id, poet_number):
    mysql_connection = get_db_connection()
    stmt = update(User).where(User.user_id == user_id).values(favorite_poet=poet_number)
    mysql_connection.session.execute(stmt)
    mysql_connection.session.commit()
    mysql_connection.session.close()
    logger.info("updated user favorite poet")


def send_poem_to_all_users():
    logger.info("scheduler started sending poems")
    mysql_connection = get_db_connection()
    all_users = mysql_connection.session.query(User).all()
    for user in all_users:
        try:
            send_poem_to_user(user.chat_id, user.favorite_poet)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
    logger.info("scheduler ended sending poems")


def get_db_connection():
    connector = DBConnector(host=os.getenv("MYSQL_HOST"),
                            user=os.getenv("MYSQL_USER"),
                            password=os.getenv("MYSQL_PASSWORD"),
                            database=os.getenv("MYSQL_DB")
                            )
    logger.info("connected to mysql")
    connector.create_session()
    return connector


def establish_db_connection():
    connector = get_db_connection()
    base = get_base()
    base.metadata.create_all(connector.engine)
    logger.info("created all schemas")
    connector.session.close()
    logger.info("closing section")
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
    scheduled_time = get_time(hour=22, minute=40, second=0)
    schedule.every().day.at(str(scheduled_time)).do(send_poem_to_all_users)

    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    logger = initialize_logger()
    Thread(target=run_scheduler).start()
    bot.infinity_polling()
