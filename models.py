"""
models.py
Core database management and query handling with strict relational mappings.
Supports University-to-College parent-child hierarchy and clean lookups.
"""

import sqlite3
import hashlib

def get_db_connection():
    # Detect exact environment path
    import os
    db_path = "school_db.sqlite" if os.path.exists("school_db.sqlite") else "school.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

class DuplicateEmailError(Exception): pass
class NotFoundError(Exception): pass
class AuthError(Exception): pass

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role="user", university_id=None, college_id=None):
    conn = get_db_connection()
    try:
        # Check if user already exists
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            raise DuplicateEmailError("User already exists")
            
        conn.execute(
            "INSERT INTO users (username, password_hash, role, university_id, college_id) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), role, university_id, college_id)
        )
        conn.commit()
    finally:
        conn.close()

# ---------- REGISTER TENANTS (WITH HIERARCHY) ----------

def add_university(code, name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO universities (university_code, university_name) VALUES (?, ?)",
            (code, name)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def add_college(university_id, college_code, college_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Strict mapping inside selected university parent node
        cursor.execute(
            "INSERT INTO colleges (university_id, college_code, college_name) VALUES (?, ?, ?)",
            (int(university_id), college_code, college_name)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

# ---------- STUDENT REGISTRY OPERATIONS ----------

def add_student(first_name, last_name, email, university_id, college_id, department=None, cgpa=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Email collision verification
        cursor.execute("SELECT student_id FROM students WHERE email = ?", (email,))
        if cursor.fetchone():
            raise DuplicateEmailError("Student with this email already registered.")
            
        cursor.execute(
            """INSERT INTO students 
               (first_name, last_name, email, university_id, college_id, department, cgpa) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (first_name, last_name, email, int(university_id), int(college_id), department, cgpa)
        )
        conn.commit()
    finally:
        conn.close()

def delete_student(student_id):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.commit()
    finally:
        conn.close()

# ---------- DROPDOWN DATA FETCHERS ----------

def get_all_universities():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM universities ORDER BY university_name ASC;").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_all_colleges():
    conn = get_db_connection()
    try:
        # Fetches colleges along with their parent university name
        sql = """
            SELECT c.*, u.university_name 
            FROM colleges c
            JOIN universities u ON c.university_id = u.university_id
            ORDER BY c.college_name ASC;
        """
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

# ---------- DYNAMIC DRILLDOWN SEARCH ----------

def get_all_students():
    conn = get_db_connection()
    sql = """
        SELECT 
            s.student_id, s.first_name, s.last_name, s.email, s.department, s.cgpa,
            u.university_name, c.college_name
        FROM students s
        LEFT JOIN universities u ON s.university_id = u.university_id
        LEFT JOIN colleges c ON s.college_id = c.college_id
        ORDER BY s.student_id DESC;
    """
    try:
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def search_students(query_str):
    conn = get_db_connection()
    sql = """
        SELECT 
            s.student_id, s.first_name, s.last_name, s.email, s.department, s.cgpa,
            u.university_name, c.college_name
        FROM students s
        LEFT JOIN universities u ON s.university_id = u.university_id
        LEFT JOIN colleges c ON s.college_id = c.college_id
        WHERE 
            s.first_name LIKE ? OR 
            s.last_name LIKE ? OR 
            s.email LIKE ? OR 
            s.department LIKE ? OR
            u.university_name LIKE ? OR
            c.college_name LIKE ?
        ORDER BY s.student_id DESC;
    """
    match_str = f"%{query_str}%"
    try:
        rows = conn.execute(sql, (match_str, match_str, match_str, match_str, match_str, match_str)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()