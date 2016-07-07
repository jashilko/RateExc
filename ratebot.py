# -*- coding: utf-8 -*-

import shelve
import config
import telebot
from telebot import types
import re
import time
import os
import flask
from flask import Flask, request

from ftplib import FTP
from io import StringIO
from bs4 import BeautifulSoup

#Настройки веб-сервера.
WEBHOOK_HOST = 'rateexc-jashilko.c9users.io'
#WEBHOOK_HOST = 'cofbot.herokuapp.com'
WEBHOOK_PORT = 80  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

# Задаем имена переменных. 
bot = telebot.TeleBot(config.token)
app = flask.Flask(__name__)

# Process webhook calls
@app.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_messages(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8")).message
        ])
    return "!", 200


# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Привет, ')
    
# Handle '/getrate'
@bot.message_handler(commands=['getrate'])
def send_getrate(message):
    try:
        bot.send_message(message.chat.id, getrate(), parse_mode='HTML')    
    except Exception as e:
        print("Ошибка commands=getrate : %s" %str(e))   
        
# Генерация меню
def generate_markup(what):
    markup = types.ReplyKeyboardMarkup()
    if what == '1':
        markup.row('Капучино', 'Латте')
        markup.row("Американо")
        markup.row('Капучино + Сэндвич = 250')
        markup.row('Отмена!')

    elif what == '2':
        markup.row('*** Большой ***')
        markup.row('** Средний **')
        markup.row('Отмена!')
    elif what == '3':
        markup.row('5', '10', '15')
        markup.row('я уже тут!')
        markup.row('Отмена!')
    elif what == '4':
        markup.add(types.KeyboardButton('Отправить номер телефона', True))
        markup.add(types.KeyboardButton('Не хочу'))
        markup.row('Отмена!')
    elif what == '5':
        markup.row('Все в силе!')
        markup.row('Отмена!')

    return markup
    
def getrate():    
    try:
        path = '/www/mosexibank.ru/rateExc.txt'
        ftp = FTP("31.31.196.33") 
        ftp.login("u2458235", "aGeKIqt7") 
        r = StringIO()
        ftp.retrlines("RETR " + path, r.write)
        ftp.quit()
        
        doc = r.getvalue()
        soup = BeautifulSoup(doc, 'html.parser')
        res = soup.find_all("td", align="center")
    
        return 'Покупка\t' + 'Продажа\n'+ '<b>USD:</b>\t' + res[2].string + '\t' + res[3].string + '\n' + '<b>EUR:</b>\t' + res[4].string + '\t' + res[5].string + '\n'
    except Exception as e:
        print("Ошибка функции getrate : %s" %str(e))         

app.run(host="0.0.0.0", port=os.environ.get('PORT', 5001))