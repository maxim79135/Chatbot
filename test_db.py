#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

conn = sqlite3.connect("mydatabase.db")
cursor = conn.cursor()

#  cursor.execute('CREATE TABLE users (telegam_id, stud_group)')
cursor.execute('CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, stud_group TEXT)')
cursor.execute("""CREATE TABLE IF NOT EXISTS feedbacks (
               id INTEGER PRIMARY KEY,
               user_id INTEGER NOT NULL,
               feedback TEXT,
               sent CHECK(sent in ("positive", "negative", "neutral")),
               FOREIGN KEY (user_id) REFERENCES users(tg_id))""")
conn.commit()



tg_id = 234234234
st_group = 'bdn-3434-12-42'
query = (f'INSERT OR IGNORE INTO users (tg_id, stud_group) values ({tg_id}, "{st_group}")')
cursor.execute(query)
conn.commit()
query = (f'INSERT INTO feedbacks (user_id, feedback, sent) values ({2332}, "хуета", "negative")')
cursor.execute(query)
#  cursor.execute(f'INSERT INTO users (telegam_id, stud_group) values ({tg_id}, {st_group})')
conn.commit()

cursor.execute(f'SELECT * FROM feedbacks WHERE user_id={tg_id}')
print(cursor.fetchone())
cursor.execute(f'SELECT * FROM users WHERE tg_id={23}')
#  cursor.execute(f'SELECT * FROM users WHERE tg_id={tg_id}')

res = cursor.fetchone()
if res:
    print('eeee')
else:
    print('nnnn')

cursor.execute('SELECT * FROM users WHERE tg_id=(?)', (tg_id,))
print(cursor.fetchone())

cursor.execute('UPDATE users SET stud_group=(?) WHERE tg_id=(?)', (None, tg_id,))
conn.commit()

cursor.execute('SELECT * FROM users WHERE tg_id=(?)', (tg_id,))
print(cursor.fetchall())

cursor.execute('INSERT OR IGNORE INTO users (tg_id, stud_group) values (?, ?)', (tg_id, st_group,))

cursor.execute('SELECT * FROM users WHERE tg_id=(?)', (232,))

conn.close()
print(cursor.fetchall())
