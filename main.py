import logging
import os
import requests
import telebot
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

WELCOME_TEXT = "سلام! به این بات خوش اومدی!"
GANJOOR_API_URL = "https://api.ganjoor.net"

def get_random_poem():
    response = requests.get(f"{GANJOOR_API_URL}/api/ganjoor/poem/random", params={"poetId": 7})
    if response.status_code == 200:
        logger.info("Sent poem.")
        return response.json()
    logger.error("Failed to get random poem")
    return ""

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, WELCOME_TEXT)


@bot.message_handler(commands=['send_poem'])
def start_sending_audio(message):
    poem_dict = get_random_poem()
    poem_text = poem_dict["plainText"]
    poem_title = poem_dict["fullTitle"]
    bot.reply_to(message, f"{poem_text}\n*{poem_title}*", parse_mode='Markdown')


# @bot.message_handler(content_types=['audio'])
# def handle_audios(message):
#     user_id = message.from_user.id
#     user_audios = get_user_audio_info(user_id)
#     logger.info(f"User {user_id} sent an audio.")
#     if len(user_audios):
#         store_user_audio_info(user_id, get_audio_info(message.audio))
#     else:
#         bot.reply_to(message, get_audio_info(message.audio))



if __name__ == '__main__':
    bot.infinity_polling()