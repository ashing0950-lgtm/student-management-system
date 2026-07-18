"""
database.py
Database connection configuration and initialization schema scripts.
"""

import sqlite3
import os

DB_NAME = "database.db"  # Agar aapka database file name alag hai toh yahan badal sakte hain

def get_connection():
    """Returns a secure sqlite3 connection object with row factory enabled."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Isse query ka result dict ki tarah access hota hai
    return conn

def initialize_database():
    """
    Creates the updated multi-tenant schema tables if they do not exist
    and applies incremental migration updates to existing structures.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Enable Foreign Key Constraints inside SQLite engine
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 2. Create Universities Table (New Top-Tier Layer)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS universities (
        university_id INTEGER PRIMARY KEY AUTOINCREMENT,
        university_code TEXT UNIQUE NOT NULL,
        university_name TEXT NOT NULL
    );
    """)

    # 3. Create Colleges Table (New Sub-Tier Layer)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS colleges (
        college_id INTEGER PRIMARY KEY AUTOINCREMENT,
        university_id INTEGER NOT NULL,
        college_code TEXT UNIQUE NOT NULL,
        college_name TEXT NOT NULL,
        FOREIGN KEY (university_id) REFERENCES universities (university_id) ON DELETE CASCADE
    );
    """)

    # 4. Create Standard Legacy Users Table (Upgraded with isolation tags)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        university_id INTEGER,
        college_id INTEGER,
        created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (university_id) REFERENCES universities (university_id),
        FOREIGN KEY (college_id) REFERENCES colleges (college_id)
    );
    """)

    # 5. Create Core Legacy Tables if they don't exist yet
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        date_of_birth TEXT,
        phone TEXT,
        address TEXT,
        department TEXT,
        enrollment_year INTEGER,
        cgpa REAL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        credits INTEGER DEFAULT 3
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        grade TEXT,
        UNIQUE(student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
    );
    """)

    # =========================================================================
    # DYNAMIC MIGRATION LAYER: Puraani 'students' table mein columns add karna
    # =========================================================================
    # Agar aapka app pehle se chal raha tha, toh 'students' table mein 
    # university_id aur college_id nahi honge. Niche ka block check karke inhe safe add karega.
    try:
        cursor.execute("SELECT university_id FROM students LIMIT 1;")
    except sqlite3.OperationalError:
        # Matlab column nahi mila, toh add karo
        print("[Migration] Adding missing multi-tenant fields to students table...")
        cursor.execute("ALTER TABLE students ADD COLUMN university_id INTEGER REFERENCES universities(university_id);")
        cursor.execute("ALTER TABLE students ADD COLUMN college_id INTEGER REFERENCES colleges(college_id);")

    conn.commit()
    conn.close()
    print("[Database] Initialization complete. Relational models active.")

if __name__ == "__main__":
    # Script ko direct run karke database tables verify karne ke liye
    initialize_database()