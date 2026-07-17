"""
models.py
Data-access layer: all CRUD operations for universities, colleges, students, courses, and enrollments.
"""

import sqlite3
from database import get_connection
from auth import hash_password, verify_password


class DuplicateEmailError(Exception):
    pass


class NotFoundError(Exception):
    pass


class AuthError(Exception):
    pass


# ---------- AUTH / USERS ----------

def verify_login(username, password):
    """Return the user row (dict) if credentials are valid, else None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def create_user(username, password, role="admin", university_id=None, college_id=None):
    """Created users can now be isolated by university or college."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role, university_id, college_id) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), role, university_id, college_id),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"Username '{username}' is already taken.")
    finally:
        conn.close()


def get_all_users(university_id=None):
    """Fetch users filtered by the active university boundary."""
    conn = get_connection()
    if university_id:
        rows = conn.execute(
            "SELECT user_id, username, role, created_on FROM users WHERE university_id = ? ORDER BY user_id", 
            (university_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT user_id, username, role, created_on FROM users ORDER BY user_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def change_password(username, current_password, new_password):
    user = verify_login(username, current_password)
    if not user:
        raise AuthError("Current password is incorrect.")
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (hash_password(new_password), user["user_id"]),
    )
    conn.commit()
    conn.close()


def delete_user(username):
    conn = get_connection()
    cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise NotFoundError(f"No user with username '{username}'.")


# ---------- UNIVERSITIES (NEW LAYER) ----------

def add_university(university_code, university_name):
    """Register a new dynamic university under the Super-Admin panel."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO universities (university_code, university_name) VALUES (?, ?)",
            (university_code.upper().strip(), university_name.strip()),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"University code '{university_code}' already exists.")
    finally:
        conn.close()


def get_all_universities():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM universities ORDER BY university_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- COLLEGES (NEW LAYER) ----------

def add_college(university_id, college_code, college_name):
    """Onboard a college linked directly to its parent university structural node."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO colleges (university_id, college_code, college_name) VALUES (?, ?, ?)",
            (university_id, college_code.upper().strip(), college_name.strip()),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"College code '{college_code}' already exists in the system.")
    finally:
        conn.close()


def get_colleges_by_university(university_id):
    """Fetch colleges belonging exclusively to the requested tenant context."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM colleges WHERE university_id = ? ORDER BY college_id", 
        (university_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- STUDENTS (UPGRADED WITH ISOLATION) ----------

def add_student(first_name, last_name, email, university_id, college_id, date_of_birth=None, 
                phone=None, address=None, department=None, enrollment_year=None, cgpa=None,
                external_id=None):
    """Inserts a student uniquely mapped to both a college and university engine footprint."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO students (external_id, first_name, last_name, email, university_id, college_id, "
            "date_of_birth, phone, address, department, enrollment_year, cgpa) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (external_id, first_name, last_name, email, university_id, college_id, date_of_birth, phone,
             address, department, enrollment_year, cgpa),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"A student with email '{email}' already exists.")
    finally:
        conn.close()


def bulk_import_students(records, default_university_id, default_college_id):
    """
    Insert many students at once with strict relational integrity verification.
    Handles fallbacks cleanly if individual row dictionary definitions miss structural tokens.
    """
    conn = get_connection()
    inserted = 0
    skipped = []
    try:
        for rec in records:
            try:
                # Fallback to defaults if tenant information isn't explicitly defined in the file row
                uni_id = rec.get("university_id") or default_university_id
                col_id = rec.get("college_id") or default_college_id
                
                conn.execute(
                    "INSERT INTO students (external_id, first_name, last_name, email, university_id, college_id, "
                    "date_of_birth, phone, address, department, enrollment_year, cgpa) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        rec.get("external_id"),
                        rec.get("first_name"),
                        rec.get("last_name"),
                        rec.get("email"),
                        uni_id,
                        col_id,
                        rec.get("date_of_birth"),
                        rec.get("phone"),
                        rec.get("address"),
                        rec.get("department"),
                        rec.get("enrollment_year"),
                        rec.get("cgpa"),
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError as e:
                skipped.append((rec, str(e)))
        conn.commit()
    finally:
        conn.close()
    return inserted, skipped


def get_all_students(university_id=None, college_id=None):
    """Secures data boundaries by isolating lookups at university or college context tiers."""
    conn = get_connection()
    if college_id:
        rows = conn.execute("SELECT * FROM students WHERE college_id = ? ORDER BY student_id", (college_id,)).fetchall()
    elif university_id:
        rows = conn.execute("SELECT * FROM students WHERE university_id = ? ORDER BY student_id", (university_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY student_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student(student_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM students WHERE student_id = ?", (student_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise NotFoundError(f"No student with id {student_id}.")
    return dict(row)


def update_student(student_id, **fields):
    if not fields:
        return
    allowed = {"first_name", "last_name", "email", "date_of_birth", "phone",
               "address", "department", "enrollment_year", "cgpa", "university_id", "college_id"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [student_id]

    conn = get_connection()
    try:
        cur = conn.execute(
            f"UPDATE students SET {set_clause} WHERE student_id = ?", values
        )
        conn.commit()
        if cur.rowcount == 0:
            raise NotFoundError(f"No student with id {student_id}.")
    except sqlite3.IntegrityError:
        raise DuplicateEmailError("That email or constraint boundary configuration error occurred.")
    finally:
        conn.close()


def delete_student(student_id):
    conn = get_connection()
    cur = conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise NotFoundError(f"No student with id {student_id}.")


def search_students(keyword, university_id=None):
    """Enforces search operations to run completely enclosed within the user's active university layer."""
    conn = get_connection()
    like = f"%{keyword}%"
    if university_id:
        rows = conn.execute(
            "SELECT * FROM students WHERE university_id = ? AND (first_name LIKE ? OR last_name LIKE ? "
            "OR email LIKE ?) ORDER BY student_id",
            (university_id, like, like, like),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM students WHERE first_name LIKE ? OR last_name LIKE ? "
            "OR email LIKE ? ORDER BY student_id",
            (like, like, like),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- COURSES ----------

def add_course(course_code, course_name, credits=3):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO courses (course_code, course_name, credits) VALUES (?, ?, ?)",
            (course_code, course_name, credits),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"Course code '{course_code}' already exists.")
    finally:
        conn.close()


def get_all_courses():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM courses ORDER BY course_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_course(course_id):
    conn = get_connection()
    cur = conn.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise NotFoundError(f"No course with id {course_id}.")


# ---------- ENROLLMENTS ----------

def enroll_student(student_id, course_id, grade=None):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO enrollments (student_id, course_id, grade) VALUES (?, ?, ?)",
            (student_id, course_id, grade),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "FOREIGN KEY" in msg:
            raise NotFoundError("Invalid student_id or course_id.")
        raise DuplicateEmailError("That student is already enrolled in this course.")
    finally:
        conn.close()


def set_grade(student_id, course_id, grade):
    conn = get_connection()
    cur = conn.execute(
        "UPDATE enrollments SET grade = ? WHERE student_id = ? AND course_id = ?",
        (grade, student_id, course_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise NotFoundError("Enrollment record not found.")


def get_student_transcript(student_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT c.course_code, c.course_name, c.credits, e.grade
        FROM enrollments e
        JOIN courses c ON c.course_id = e.course_id
        WHERE e.student_id = ?
        ORDER BY c.course_code
        """,
        (student_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_course_roster(course_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.student_id, s.first_name, s.last_name, s.email, e.grade
        FROM enrollments e
        JOIN students s ON s.student_id = e.student_id
        WHERE e.course_id = ?
        ORDER BY s.last_name
        """,
        (course_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]