import sqlite3
import hashlib
import os

def get_db_connection():
    # Maine aapko sujhaav diya tha ki file ka naam fix kar lo
    # taaki confusion na ho
    conn = sqlite3.connect("database.db") 
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    conn = get_db_connection()
    # Print karke dekho terminal mein kya username/hash aa raha hai
    print(f"DEBUG: Checking {username} with hash {hash_password(password)}")
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", 
                        (username, hash_password(password))).fetchone()
    conn.close()
    return dict(user) if user else None

def add_user(username, password, role='user'):
    conn = get_db_connection()
    # Password ko hash karna zaroori hai
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                 (username, hashed_pw, role))
    conn.commit()
    conn.close()

# models.py mein ye query update karo
def get_students_by_role(user_session):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    u_id = user_session.get('user_id')
    role = user_session.get('role')
    
    query = """SELECT s.*, c.college_name 
               FROM students s 
               LEFT JOIN colleges c ON s.college_id = c.college_id"""
    
    if role != 'admin':
        query += " WHERE s.created_by = ? ORDER BY s.student_id DESC"
        rows = conn.execute(query, (u_id,)).fetchall()
    else:
        query += " ORDER BY s.student_id DESC"
        rows = conn.execute(query).fetchall()
        
    conn.close()
    return [dict(r) for r in rows]

def add_student(first_name, last_name, email, department, cgpa, created_by, college_id):
    conn = get_db_connection()
    conn.execute("""INSERT INTO students (first_name, last_name, email, department, cgpa, created_by, college_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                 (first_name, last_name, email, department, cgpa, created_by, college_id))
    conn.commit()
    conn.close()

def delete_student(student_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

def get_student_by_id(student_id):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    return dict(student) if student else None

def get_all_colleges():
    conn = get_db_connection() # Ya jo bhi aapka connection function hai
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM colleges").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_students_by_role(user_session):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row # Taaki data dictionary ki tarah mile
    u_id = user_session.get('user_id')
    role = user_session.get('role')
    
    # Query: students aur colleges table ko join kiya taaki name dikh sake
    query = """SELECT s.*, c.college_name 
               FROM students s 
               LEFT JOIN colleges c ON s.college_id = c.college_id """
    
    if role != 'admin':
        query += " WHERE s.created_by = ?"
        rows = conn.execute(query + " ORDER BY s.student_id DESC", (u_id,)).fetchall()
    else:
        rows = conn.execute(query + " ORDER BY s.student_id DESC").fetchall()
        
    conn.close()
    return [dict(r) for r in rows]