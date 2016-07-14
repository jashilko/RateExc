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
from config import shelve_status
from config import shelve_orderid
import utils
from PSQLighter import PSQLighter

from ftplib import FTP
from io import StringIO
from bs4 import BeautifulSoup

#Статусы 
Status_RateChoosed = 1 # Выбрано что купить или продать // Выводим: вопрос сколько
Status_VolumeChoosed = 2 # Выбрано количество валюты // Выводим: сумму сделки.
Status_ShowSumma = 3 # Выбрано время // Выводим Подтверждение. 
Status_ConfirmChoose = 4 # Выбрано подтверждение // Выводим пока.
Status_OfferSandwich = 61 # Выбраны сэндвич + капучино // Выводим время.


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
    bot.send_message(message.chat.id, 'Привет!')
    
# Handle '/getrate'
@bot.message_handler(commands=['getrate'])
def send_getrate(message):
    try:
        if getrate() == '':
            mes = 'Сейчас курсы не заданы'
        else:
            mes = getrate()
        markup = generate_markup(Status_RateChoosed)
        bot.send_message(message.chat.id, mes, parse_mode='HTML', reply_markup=markup)  
        # Записываем статус 0 - никаких действий пока не совершено. 
        utils.set_storage(shelve_status, message.chat.id, Status_RateChoosed)
    except Exception as e:
        print("Ошибка commands=getrate : %s" %str(e))   

# Обработка любого присланного текста
@bot.message_handler(func=lambda message: True)
def read_message(message):

    #Получаем статус-состояние. 
    idstatus = utils.get_storage(shelve_status, message.chat.id)
    if idstatus is not None:
        print ("Begin status - " + str(idstatus))

    # Класс БД
    db_worker = PSQLighter()
    
    # Проверяем, не нажал ли пользователь "Отмену!"
    if message.text == 'Отмена!':
        try:
            #markup = generate_markup(Status_None)
            # Удаляем запись в БД, записи в обоих хранилищах.
            #if (get_storage(shelve_dbid, message.chat.id) is not None):
            #    db_worker.del_order(int(get_storage(shelve_dbid, message.chat.id)))
            utils.del_storage(shelve_status, message.chat.id)
            #set_storage_orderstat(message.chat.id, Status_None)
            utils.del_storage(shelve_status, message.chat.id)
            #bot.send_message(message.chat.id, 'Вы можете оформить новый заказ: ', reply_markup=markup)

        except Exception as e:
            print("Ошибка Отмена! : %s" %str(e))     
        
    elif (idstatus == Status_RateChoosed):
        try:
            # Парсим сообщение типа "Продать $ за ...."
            if message.text.find('Продать') >= 0:
                vector_str = 'продать'
                vector = 0
                if message.text.find('$') >= 0:
                    cur = 'USD'
                    rate = getrate(1)
                elif message.text.find('€') >= 0:
                    cur = 'EUR'
                    rate = getrate(3)
                else:
                    cur = ''
            elif message.text.find('Купить') >= 0:
                vector_str = 'купить'
                vector = 1
                if message.text.find('$') >= 0:
                    cur = 'USD'
                    rate = getrate(2)
                elif message.text.find('€') >= 0:
                    cur = 'EUR'
                    rate = getrate(4)
                else:
                    cur = ''
            else:
                vector = -1

            if (vector > -1) and (cur != ''):
                # Записываем выбор клиента в базу. 
                id = db_worker.set_order(None, message.from_user.id, cur, rate, vector, None, None, None)            
                if id is not None:
                    utils.set_storage(shelve_orderid, message.chat.id, id)

            
            utils.set_storage(shelve_status, message.chat.id, Status_VolumeChoosed)

            markup = generate_markup(Status_VolumeChoosed)
            bot.send_message(message.chat.id, "Сколько вы хотите " + vector_str + " " + cur + "?", reply_markup=markup)  
            
        except Exception as e:
            print("Ошибка Status_RateChoosed! : %s" %str(e))     
    elif (idstatus == Status_VolumeChoosed):
        try:
            # Проверяем, является ли введенный текст числом.
            if re.match(r'[1-9]{1}\d{1}', message.text):
                
                id = utils.get_storage(shelve_orderid, message.from_user.id)
                rate = db_worker.get_column(id, 3)
                summa = float(rate) * int(message.text)
                
                db_worker.set_order(id, message.from_user.id, None, None, None, message.text, summa, None)
                utils.set_storage(shelve_status, message.chat.id, Status_ShowSumma)
                markup = generate_markup(Status_ShowSumma)
                v = db_worker.get_column(id, 4)
                if v == 0:
                    bot.send_message(message.chat.id, 'Сумма за прожажу валюты: ' + str(summa)  + ' рублей', reply_markup=markup)  
                else:
                    bot.send_message(message.chat.id, 'Сумма за покупку валюты: ' + str(summa)  + ' рублей', reply_markup=markup)  
                
            else:
                print("Вы ввели не число")

            
                        
        except Exception as e:
            print("Ошибка Status_VolumeChoosed! : %s" %str(e))     
    
    
    

            
    db_worker.close()
    idstatus = utils.get_storage(shelve_status, message.chat.id)
    if idstatus is not None:
        print ("End status - " + str(idstatus))
    
        
        
# Генерация меню
def generate_markup(what):
    markup = types.ReplyKeyboardMarkup()
    if what == Status_RateChoosed:
        markup.row('Продать $ за ' + getrate(1), 'Купить $ за ' + getrate(2))
        markup.row('Продать € за ' + getrate(3), 'Купить € за ' + getrate(4))
        markup.row('Отмена!')
    elif what == Status_VolumeChoosed:
        markup.row('10', "20")
        markup.row('50', "100")
        markup.row('Отмена!')
    elif what == Status_ShowSumma:
        markup.row('Согласен')
        markup.row('Изменить')
        markup.row('Отмена!')
    elif what == '4':
        markup.add(types.KeyboardButton('Отправить номер телефона', True))
        markup.add(types.KeyboardButton('Не хочу'))
        markup.row('Отмена!')
    elif what == '5':
        markup.row('Все в силе!')
        markup.row('Отмена!')

    return markup
    
def getrate(num = 0):    
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
    
        if num > 0:
            return res[num + 1].string
        else:
            return 'Продать\t' + 'Купить\n'+ '<b>USD:</b>\t' + res[2].string + '\t' + res[3].string + '\n' + '<b>EUR:</b>\t' + res[4].string + '\t' + res[5].string + '\n'
    except Exception as e:
        print("Ошибка функции getrate : %s" %str(e))  
        return ''

app.run(host="0.0.0.0", port=os.environ.get('PORT', 5001))