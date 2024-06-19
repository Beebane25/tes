from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Membuat atau menghubungkan ke database
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Membuat tabel users dan text_data jika belum ada
def create_tables():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS text_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        data TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.close()

create_tables()

# Endpoint untuk menerima file teks
@app.route('/upload_text', methods=['POST'])
def upload_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.txt'):
        text_content = file.read().decode('utf-8')
        user_id = request.form.get('user_id', 1)  # Assuming user_id is provided, otherwise default to 1
        conn = get_db_connection()
        conn.execute('INSERT INTO text_data (user_id, data) VALUES (?, ?)', (user_id, text_content))
        conn.commit()
        conn.close()
        return jsonify({"success": "File uploaded and saved successfully"}), 200
    else:
        return jsonify({"error": "File must be a text file"}), 400

# Route untuk halaman login
@app.route('/')
def halaman():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('lobby'))
        else:
            flash('Login gagal. Periksa username dan password Anda.')
            
    return render_template('login.html')

# Route untuk halaman registrasi
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            flash('Registrasi berhasil! Silakan login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Error: Username sudah ada.')
        finally:
            conn.close()
    
    return render_template('register.html')

# Route untuk halaman lobby
@app.route('/lobby', methods=['GET', 'POST'])
def lobby():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    text_data = conn.execute('SELECT * FROM text_data WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and file.filename.endswith('.txt'):
            text_content = file.read().decode('utf-8')
            conn = get_db_connection()
            conn.execute('INSERT INTO text_data (user_id, data) VALUES (?, ?)', (session['user_id'], text_content))
            conn.commit()
            conn.close()
            flash('File berhasil diunggah dan disimpan.')
            return redirect(url_for('lobby'))
        else:
            flash('File yang diunggah harus berupa file teks.')
    
    return render_template('lobby.html', username=session['username'], users=users, text_data=text_data)

# Route untuk logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
