import MySQLdb
from flask import g
from app.config import Config

def get_db():
    if 'db' not in g:
        g.db = MySQLdb.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            passwd=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB,

        )
    return g.db

#CHANGED
def close_db():
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            print("Handled DB close error:", e)


def init_db():
    """Initialize database and create tables if they don't exist"""
    db = get_db()
    cursor = db.cursor()

import pymysql

def get_db_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor  # 👈 KEY LINE
    )
