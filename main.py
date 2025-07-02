from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret-key'

# Χρήση threading ως async mode για να αποφύγουμε το eventlet error
socketio = SocketIO(app, async_mode='threading')

DB_NAME = 'mydatabase.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
            user = c.fetchone()
            if user:
                session['username'] = username
                return redirect('/chat')
            else:
                return 'Λάθος στοιχεία!'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                return redirect('/login')
            except sqlite3.IntegrityError:
                return 'Το όνομα χρήστη υπάρχει ήδη.'
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect('/login')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT username, content, timestamp FROM messages ORDER BY id ASC')
        messages = c.fetchall()
    return render_template('chat.html', username=session['username'], messages=messages)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@socketio.on('send_message')
def handle_message(data):
    username = session.get('username')
    content = data['message']
    timestamp = datetime.now().strftime('%H:%M:%S')

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO messages (username, content, timestamp) VALUES (?, ?, ?)', (username, content, timestamp))
        conn.commit()

    emit('receive_message', {'username': username, 'message': content, 'timestamp': timestamp}, broadcast=True)

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
