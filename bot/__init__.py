import logging
import telebot

from backend.settings import API_TOKEN

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(API_TOKEN)
