import os
import sqlite3
import hashlib

def get_db_connection():
    # Render par '/data' naam ka folder hota hai jab hum disk attach karte hain
    # Agar wo folder mila toh wahan save karega, nahi toh aapke computer par local folder mein
    if os.path.exists('/data'):
        db_path = '/data/database.db'
    else:
        db_path = 'database.db'
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # University column removed
    conn.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        full_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        cgpa REAL NOT NULL,
                        college TEXT NOT NULL,
                        department TEXT NOT NULL,
                        branch TEXT NOT NULL,
                        created_by TEXT NOT NULL
                    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = get_db_connection()
    try:
        pw_hash = hash_password(password)
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def authenticate_user(username, password):
    conn = get_db_connection()
    pw_hash = hash_password(password)
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", 
                        (username, pw_hash)).fetchone()
    conn.close()
    return user

def get_students(logged_in_user, search_val=None):
    conn = get_db_connection()
    query = "SELECT * FROM students"
    params = []
    
    if logged_in_user.lower() != 'ashish':
        query += " WHERE created_by = ?"
        params.append(logged_in_user)
        
    if search_val:
        if "WHERE" in query:
            query += " AND (full_name LIKE ? OR email LIKE ? OR college LIKE ?)"
        else:
            query += " WHERE (full_name LIKE ? OR email LIKE ? OR college LIKE ?)"
        params.extend(['%' + search_val + '%', '%' + search_val + '%', '%' + search_val + '%'])
        
    students = conn.execute(query, params).fetchall()
    conn.close()
    return students

def get_student_by_id(student_id):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return student

def update_student(student_id, full_name, email, age, cgpa, college, department, branch):
    conn = get_db_connection()
    conn.execute('''UPDATE students 
                    SET full_name = ?, email = ?, age = ?, cgpa = ?, college = ?, department = ?, branch = ? 
                    WHERE id = ?''', 
                 (full_name, email, age, cgpa, college, department, branch, student_id))
    conn.commit()
    conn.close()

def add_student(full_name, email, age, cgpa, college, department, branch, username):
    conn = get_db_connection()
    conn.execute('''INSERT INTO students 
                    (full_name, email, age, cgpa, college, department, branch, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                 (full_name, email, age, cgpa, college, department, branch, username))
    conn.commit()
    conn.close()

def delete_student(student_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()