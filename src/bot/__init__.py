import logging
import telebot

from src.config.settings import settings

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(settings.bot_token)