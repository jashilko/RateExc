# -*- coding: utf-8 -*-
# Файл для работы с бд

'''
 Для heroku придётся использовать базу данных,
 т.к. данные не сохраняются
'''

import psycopg2
import dj_database_url 
from datetime import datetime

# Для представления ссылки на базу в её данные (логин, пароль и т.д.) postgres://USER:PASSWORD@HOST:PORT/NAME

class PSQLighter:
    
    def __init__(self):
        try:
            #Строка для Cloud9
            #database = "dbname=ratedb user=ratedb_user password=qwerty host=localhost port=5432"
            database = "dbname=ratedb user=ratedb_user password=qwerty host=localhost port=5432"
            
            # Строка для heroku
            #database = "dbname=dcpuk30ncm8l9i user=uxwkaztpfcmjos password=9IzK-mqlx80bZ7WBTJUW3V9qEW host=ec2-204-236-228-133.compute-1.amazonaws.com port=5432"
            self.connection = psycopg2.connect(database)
            self.cursor = self.connection.cursor()
            self.connection.set_client_encoding('UTF8')
        except Exception as e:
            print("Ошибка __init__: %s" %str(e))  

    # Проверка клиента на существование.
    def check_exist_client(self, clientid):
        try:
            if clientid is not None:
                self.cursor.execute('''SELECT count(*) FROM client where id = %s;'''%(clientid))
                result = self.cursor.fetchone()      
                count = result[0]
                print ('This client count ' + str(count))
                if count > 0:
                    return True
                else:
                    return  False
            else:
                return False
        except Exception as e:
            print("Ошибка check_exist_client: %s" %str(e))  
        
            
    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()     
        
    # Пишем в базу номер клиента или самого клиента
    def set_client_phone(self,contact, username):
        try:
            """
            Добавляем телефон клиента
            :param contact: Отправленный клиентом контакт
            :param username: юзернейм клиента
            """
            if self.check_exist_client(contact.user_id):
                self.cursor.execute('''UPDATE client SET phone_number = \'%s\' WHERE id = %s;'''%(contact.phone_number, contact.user_id))
            else:
               self.cursor.execute('''INSERT INTO client(id, username, first_name, phone_number) VALUES(%s, \'%s\', \'%s\', \'%s\');'''%(contact.user_id, username, contact.first_name, contact.phone_number))
            self.connection.commit()
            return None
        except Exception as e:
            print("Ошибка set_client_phone: %s" %str(e))          

    # Записываем заказ. 
    def set_order (self, id, idclient, cur, rate, vector, volume, summa, confirm):
        """
        :return: ИД добавленной записи.
        """
        try:
            #Добавляем что.
            if (idclient is not None):
                # Вставляем заказ
                if (id is None) and (cur != '') and (rate != '') and (vector > -1):
                    dt = datetime.now()
                    self.cursor.execute('''INSERT INTO orders(idclient, cur, rate, vector, ordertime) VALUES (%s, \'%s\', %s, %s, \'%s\') RETURNING id;'''%(idclient, cur, rate, vector, dt))
                    self.connection.commit()
                    id_of_new_row = self.cursor.fetchone()[0]
                    return id_of_new_row
                # Добавляем сумму заказа
                if (int(volume) > 0) and (id is not None):
                    self.cursor.execute('''UPDATE orders SET volume = %s, summa = %s WHERE id = %s ;'''%(volume, summa, id))
                    self.connection.commit()
                    return id
                # Добавляем подтверждение
                if (confirm is not None) and (id is not None):
                    self.cursor.execute('''UPDATE orders SET confirm = %s WHERE id = %s;'''%(confirm, id))
                    self.connection.commit()                     
                    return id
            else:
                return None
        except Exception as e:
            print("Ошибка set_order: %s" %str(e))                      
        

    def get_order_string(self, id):
        try:
            vector = self.get_column(id, 4)
            cur = self.get_column(id, 2)
            rate = self.get_column(id, 3)
            summa = self.get_column(id, 6)
            volume = self.get_column(id, 5)
            
            if vector is not None:
                vector_str = 'купить ' if vector == 1 else 'продать '

            if (vector is not None) and (cur is not None) and (rate is not None) and (summa is not None) and (volume is not None):
                return 'Вы решили ' + vector_str + str(volume) + cur  + ' по ' + str(rate) + ' на сумму: ' + str(summa) + ' рублей. '
            else:
                return None
        except Exception as e:
            print("Ошибка get_order_string : %s" %str(e))  
        
    def get_column(self, id, number):
        try:
            self.cursor.execute('''SELECT * FROM orders where id = %s;'''%(id))
            res = self.cursor.fetchone()
            #if 
            return res[number]

        except Exception as e:
            print("Ошибка get_column : %s" %str(e))  


    def del_order(self, id):
        """
        Удаляем заказ.
        :param id: Id заказа.
        """
        try:
            if (id is not None):
               self.cursor.execute('''DELETE FROM orders where id = %s;'''%(id))
               self.connection.commit() 
            return None     
        except Exception as e:
            print("Ошибка del_order : %s" %str(e))          