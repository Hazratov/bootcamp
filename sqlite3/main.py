import sqlite3

def connect():
    conn = sqlite3.connect('test.db')
    return conn

conn = connect()
cursor = conn.cursor()

def create_table():
    cursor.execute('''
        create table if not exists users (
            user_id integer primary key,
            name varchar(25) not null,
            email varchar(55) not null
        )
    ''')
    conn.commit()

def insert(name, email):
    cursor.execute('''
        insert into users (name, email) 
        values (?, ?)
    ''', (name, email))
    conn.commit()

def select_all():
    cursor.execute('''
        select * from users
    ''')
    return cursor.fetchall()

def delete(user_id):
    cursor.execute('''
        delete from users where user_id = ?
    ''',(user_id,))
    conn.commit()


#create_table()
#insert('Akbar', 'Akbar@gmail.com')
delete(1)
print(select_all())