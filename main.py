import logging
import os
import requests
import telebot
from dotenv import load_dotenv
import constants
from dbconnector import DBConnector
from user import User
from user import get_base



def initialize_telebot():
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    bot = telebot.TeleBot(BOT_TOKEN)
    return bot


logger = None

bot = initialize_telebot()


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, constants.WELCOME_TEXT)


def get_random_poem():
    response = requests.get(f"{constants.GANJOOR_API_URL}/api/ganjoor/poem/random", params={"poetId": 7})
    if response.status_code == 200:
        logger.info("Sent poem.")
        return response.json()
    logger.error("Failed to get random poem")
    return ""


@bot.message_handler(commands=['send_poem'])
def start_sending_audio(message):
    poem_dict = get_random_poem()
    poem_text = poem_dict["plainText"]
    poem_title = poem_dict["fullTitle"]
    bot.reply_to(message, f"{poem_text}\n\n*{poem_title}*", parse_mode='Markdown')


# @bot.message_handler(content_types=['audio'])
# def handle_audios(message):
#     user_id = message.from_user.id
#     user_audios = get_user_audio_info(user_id)
#     logger.info(f"User {user_id} sent an audio.")
#     if len(user_audios):
#         store_user_audio_info(user_id, get_audio_info(message.audio))
#     else:
#         bot.reply_to(message, get_audio_info(message.audio))

def register_new_user():
    logger.info("user registration started")
    connector = DBConnector(host=os.getenv("MYSQL_HOST"),
                            user=os.getenv("MYSQL_USER"),
                            password=os.getenv("MYSQL_PASSWORD"),
                            database=os.getenv("MYSQL_DB")
                            )
    logger.info("connected to mysql")
    connector.create_session()
    logger.info("created a session")
    base = get_base()
    base.create_all(connector.engine)
    user = User(name='mamadoo', username='mamadoo')
    logger.info("created a user")
    connector.session.add(user)
    logger.info("added a user")
    connector.session.commit()
    logger.info("stored a user")


def initialize_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


if __name__ == '__main__':
    load_dotenv()
    logger = initialize_logger()
    register_new_user()
    # bot.infinity_polling()
