import logging
import telebot

from fastapiProject.settings import BOT_TOKEN

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)
