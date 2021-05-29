#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple database manager for Vyatsu chat-bot"""

import sqlite3
from typing import Any, List, Optional


class DBManager:
    """Helper class for using sqlite database"""

    def __init__(self, db_name='helper.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, stud_group TEXT)')
        self.cursor.execute("""
                           CREATE TABLE IF NOT EXISTS feedbacks (
                           id INTEGER PRIMARY KEY,
                           user_id INTEGER NOT NULL,
                           feedback TEXT,
                           sent CHECK(sent in ("positive", "negative", "neutral")),
                           FOREIGN KEY (user_id) REFERENCES users(tg_id))
        """)
        self.conn.commit()
        self.conn.close()

    def user_exist(self, tg_id: int) -> bool:
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT * FROM users WHERE tg_id=(?)', (tg_id,))
        res = bool(self.cursor.fetchone())
        self.conn.close()
        return res

    def insert_user(self, tg_id: int, st_group: Optional[str] = None) -> None:
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('INSERT OR IGNORE INTO users (tg_id, stud_group) values (?, ?)', (tg_id, st_group,))
        self.conn.commit()
        self.conn.close()

    def update_user(self, tg_id: int, st_group: Optional[str] = None) -> None:
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('UPDATE OR IGNORE INTO users (tg_id, stud_group) VALUES (?, ?)', (tg_id, st_group,))
        self.conn.commit()
        self.conn.close()

    def save_feedback(self, tg_id: int, feedback: str, sent: str) -> None:
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('INSERT INTO feedbacks (user_id, feedback, sent) VALUES (?, ?, ?)',
                            (tg_id, feedback, sent))
        self.conn.commit()
        self.conn.close()

    def get_user_feedbacks(self, tg_id: int) -> List[Any]:
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT * from feedbacks WHERE user_id=(?)', (tg_id,))
        res = self.cursor.fetchall()
        self.conn.close()
        return res
