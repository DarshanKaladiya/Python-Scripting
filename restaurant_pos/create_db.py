import pymysql
conn = pymysql.connect(host='127.0.0.1', user='root', password='')
cursor = conn.cursor()
cursor.execute('CREATE DATABASE IF NOT EXISTS restaurant_pos_db;')
conn.close()
