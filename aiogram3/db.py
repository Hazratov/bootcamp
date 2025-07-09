import sqlite3

def connect_db():
    conn = sqlite3.connect('test.db')
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        create table if not exists users (
            user_id integer primary key,
            user_name varchar(20) not null,
            email varchar(55) not null
            )
    ''')
    conn.commit()
    conn.close()

def insert_user(name, email):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        insert into users (user_name, email)
            values (?, ?)
    ''', (name, email)
                   )
    conn.commit()
    conn.close()

def show_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        select * from users
    ''')
    return cursor.fetchall()
