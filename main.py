import logging
import os
import requests
import telebot
from dotenv import load_dotenv
import constants
from dbconnector import DBConnector
from user import User
from user import get_base
from sqlalchemy import update

load_dotenv()


def initialize_telebot():
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    bot = telebot.TeleBot(BOT_TOKEN)
    return bot


logger = None
mysql_connection = None
bot = initialize_telebot()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_info = {
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name
    }
    register_new_user(user_info)
    bot.reply_to(message, constants.WELCOME_TEXT)
    bot.send_message(message.chat.id, constants.POEM_CHOICE_TEXT)


def get_random_poem():
    response = requests.get(f"{constants.GANJOOR_API_URL}/api/ganjoor/poem/random", params={"poetId": 7})
    if response.status_code == 200:
        logger.info("Sent poem.")
        return response.json()
    logger.error("Failed to get random poem")
    return ""


@bot.message_handler(commands=["send_now"])
def start_sending_audio(message):
    poem_dict = get_random_poem()
    poem_text = poem_dict["plainText"]
    poem_title = poem_dict["fullTitle"]
    bot.reply_to(message, f"{poem_text}\n\n*{poem_title}*", parse_mode='Markdown')


@bot.message_handler(regexp=r"(1|2|3|7)")
def set_favorite_poet(message):
    username = message.from_user.username
    response = message.text
    logger.info(f"we got {response} from a user")
    set_favorite_poet_in_db(username, response)


def register_new_user(user_info):
    mysql_connection.create_session()
    base = get_base()
    base.metadata.create_all(mysql_connection.engine)
    user = User(**user_info)
    mysql_connection.session.add(user)
    mysql_connection.session.commit()
    logger.info("New user registered")


def set_favorite_poet_in_db(username, poet_number):
    stmt = update(User).where(User.username == username).values(favorite_poet=poet_number)
    mysql_connection.session.execute(stmt)
    mysql_connection.session.commit()
    logger.info("updated user favorite poet")


def establish_db_connection():
    connector = DBConnector(host=os.getenv("MYSQL_HOST"),
                            user=os.getenv("MYSQL_USER"),
                            password=os.getenv("MYSQL_PASSWORD"),
                            database=os.getenv("MYSQL_DB")
                            )
    return connector


def initialize_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


if __name__ == '__main__':
    logger = initialize_logger()
    mysql_connection = establish_db_connection()
    bot.infinity_polling()
