import sqlite3
import bcrypt
import uuid

class Auth:
    def __init__(self):
        self.db = 'auth.sqlite'
        db = sqlite3.connect('auth.sqlite')
        cur = db.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)')
        cur.execute('CREATE TABLE IF NOT EXISTS tokens(username TEXT, ip TEXT, token TEXT)')
        db.commit()
        cur.close()
        db.close()
    
    def create_user(self, username, passwd):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(passwd.encode('utf-8'), salt).decode('utf-8')

        db = sqlite3.connect(self.db)
        cur = db.cursor()

        cur.execute('INSERT INTO users VALUES(?, ?)', (username, hashed))
        db.commit()
        cur.close()
        db.close()
    
    def delete_user(self, username):
        db = sqlite3.connect(self.db)
        cur = db.cursor()
        cur.execute('DELETE FROM users WHERE username=?', (username,))
        cur.execute('DELETE FROM tokens WHERE username=?', (username,))
        db.commit()
        cur.close()
        db.close()
    
    def login(self, username, passwd):
        db = sqlite3.connect(self.db)
        cur = db.cursor()
        cur.execute('SELECT * FROM users WHERE username=?', (username,))
        data = cur.fetchone()
        if data == None:
            return False
        hashed = data[1]
        cur.close()
        db.close()
        return bcrypt.checkpw(passwd.encode(), hashed.encode())

    def create_token(self, username, ip):
        token = str(uuid.uuid4()).replace('-', '')
        db = sqlite3.connect(self.db)
        cur = db.cursor()
        cur.execute('INSERT INTO tokens VALUES(?, ?, ?)', (username, ip, token))
        db.commit()
        cur.close()
        db.close()
        return token
    
    def verify_token(self, ip, token):
        db = sqlite3.connect(self.db)
        cur = db.cursor()
        cur.execute('SELECT * FROM tokens WHERE ip=? AND token=?', (ip, token))
        data = cur.fetchall()
        cur.close()
        db.close()
        if data == []:
            return False
        else:
            return data[0]
