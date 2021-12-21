
# import sqlite3

# sql_connection = sqlite3.connect('sqlite_python.db')
# cursor = sql_connection.cursor()
# cursor.execute("select * from statistics;")
# print(cursor)
from datetime import datetime

print(datetime.now().strptime('%D : %M : %Y'))