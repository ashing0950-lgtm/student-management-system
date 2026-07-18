"""
main.py
Full Institutional Management Control Interface with Structured Hierarchies.
"""

import sys
import os
import sqlite3
from database import initialize_database
import models
from models import DuplicateEmailError, NotFoundError, AuthError
from flask import Flask, render_template_string, request, redirect, url_for, flash

# ---------- AUTOMATIC DATABASE STRUCTURE VALIDATION & PATCH ----------
def patch_and_seed_database():
    """Ensures relational tables and relational hierarchy are strictly active on production storage."""
    try:
        db_path = "school_db.sqlite" if os.path.exists("school_db.sqlite") else "school.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Base Multi-tenant structural tables check
        cursor.execute("CREATE TABLE IF NOT EXISTS universities (university_id INTEGER PRIMARY KEY AUTOINCREMENT, university_code TEXT UNIQUE, university_name TEXT);")
        cursor.execute("CREATE TABLE IF NOT EXISTS colleges (college_id INTEGER PRIMARY KEY AUTOINCREMENT, university_id INTEGER, college_code TEXT UNIQUE, college_name TEXT, FOREIGN KEY(university_id) REFERENCES universities(university_id));")
        
        # 2. Synchronize columns in users/students tables if missed in legacy setup
        cursor.execute("PRAGMA table_info(students);")
        student_cols = [c[1] for c in cursor.fetchall()]
        if "university_id" not in student_cols:
            cursor.execute("ALTER TABLE students ADD COLUMN university_id INTEGER DEFAULT 1;")
        if "college_id" not in student_cols:
            cursor.execute("ALTER TABLE students ADD COLUMN college_id INTEGER DEFAULT 1;")
            
        cursor.execute("PRAGMA table_info(users);")
        user_cols = [c[1] for c in cursor.fetchall()]
        if "university_id" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN university_id INTEGER DEFAULT 1;")
        if "college_id" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN college_id INTEGER DEFAULT 1;")
            
        # 3. Insert default placeholder rows if completely empty
        cursor.execute("SELECT count(*) FROM universities;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO universities (university_id, university_code, university_name) VALUES (1, 'BBDU', 'Babu Banarasi Das University');")
            cursor.execute("INSERT INTO colleges (college_id, university_id, college_code, college_name) VALUES (1, 1, 'BBDU-CSE', 'School of Engineering (CSE Branch)');")
            
        conn.commit()
        conn.close()
        print("[Database Multi-Tenant Engine] Hierarchy sync active.")
    except Exception as e:
        print(f"[Database Setup Warning] {str(e)}")

# Safe bootstrap initialization execution
initialize_database()
patch_and_seed_database()
try:
    models.create_user("admin", "admin123", "superadmin")
except DuplicateEmailError:
    pass

# ---------- WEB SERVER APPLICATION ----------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sms_super_secret_key_prod_123")

HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>SMS Multi-Tenant Portal</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f9; color: #333; }
        .navbar { background-color: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        .navbar h2 { margin: 0; font-size: 20px; }
        .main-container { max-width: 1300px; margin: 30px auto; padding: 0 20px; display: grid; grid-template-columns: 1.1fr 2fr; gap: 25px; }
        @media(max-width: 1000px) { .main-container { grid-template-columns: 1fr; } }
        .card { background: white; padding: 22px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
        h3 { margin-top: 0; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; font-size: 16px; }
        .form-group { margin-bottom: 12px; }
        label { display: block; margin-bottom: 4px; font-weight: 600; font-size: 13px; color: #34495e; }
        input, select { width: 100%; padding: 8px 12px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; background-color: #fff; }
        .btn { background-color: #3498db; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; display: inline-block; text-align: center; text-decoration: none; box-sizing: border-box; }
        .btn:hover { background-color: #2980b9; }
        .btn-danger { background-color: #e74c3c; padding: 5px 10px; font-size: 11px; width: auto; border-radius: 3px; }
        .btn-danger:hover { background-color: #c0392b; }
        .btn-secondary { background-color: #2ecc71; }
        .btn-secondary:hover { background-color: #27ae60; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; font-size: 14px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; vertical-align: middle; }
        th { background-color: #f8f9fa; color: #2c3e50; font-weight: 700; }
        .alert { padding: 12px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 20px; font-size: 14px; border: 1px solid #c3e6cb; }
        .alert-danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        .search-box input { flex: 1; }
        .search-box .btn { width: auto; }
        .inst-badge { background: #ebf5fb; color: #2e86de; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; margin-bottom: 2px; }
        .clg-badge { background: #f4f6f7; color: #7f8c8d; padding: 3px 8px; border-radius: 4px; font-size: 11px; display: inline-block; }
    </style>
</head>
<body>

    <div class="navbar">
        <h2>🎓 Multi-Tenant Student Registry Engine</h2>
        <div><strong>Node Control:</strong> Fully Hierarchical Structure</div>
    </div>

    <div class="main-container">
        <div class="sidebar">
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert {% if category == 'error' %}alert-danger{% endif %}">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}

            <div class="card">
                <h3>🏢 1. Register University Parent Node</h3>
                <form action="/add-university" method="POST">
                    <div class="form-group">
                        <label>University Code (e.g., BBDU, AKTU)</label>
                        <input type="text" name="uni_code" placeholder="Enter Unique Short Code" required>
                    </div>
                    <div class="form-group">
                        <label>University Full Name</label>
                        <input type="text" name="uni_name" placeholder="Enter Official Name" required>
                    </div>
                    <button type="submit" class="btn btn-secondary">Onboard University</button>
                </form>
            </div>

            <div class="card">
                <h3>🏫 2. Map College Under University</h3>
                <form action="/add-college" method="POST">
                    <div class="form-group">
                        <label>Select Parent University</label>
                        <select name="parent_uni_id" required>
                            {% for u in universities %}
                                <option value="{{ u.university_id }}">{{ u.university_name }} ({{ u.university_code }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>College Code (e.g., BBDEC, BBDNITM)</label>
                        <input type="text" name="clg_code" placeholder="Enter College Branch Code" required>
                    </div>
                    <div class="form-group">
                        <label>College Full Name</label>
                        <input type="text" name="clg_name" placeholder="Enter College Campus Name" required>
                    </div>
                    <button type="submit" class="btn btn-secondary" style="background-color: #9b59b6;">Map Branch Location</button>
                </form>
            </div>

            <div class="card">
                <h3>👤 3. Register Student Record</h3>
                <form action="/add-student" method="POST">
                    <div class="form-group">
                        <label>First Name</label>
                        <input type="text" name="first_name" required>
                    </div>
                    <div class="form-group">
                        <label>Last Name</label>
                        <input type="text" name="last_name" required>
                    </div>
                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>Assigned Institutional Campus Branch</label>
                        <select name="target_college_id" required>
                            {% for c in colleges %}
                                <option value="{{ c.college_id }}">{{ c.university_name }} ➔ {{ c.college_name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Department</label>
                        <input type="text" name="department" placeholder="e.g. CSE-AI" required>
                    </div>
                    <div class="form-group">
                        <label>Current CGPA</label>
                        <input type="number" step="0.01" name="cgpa" placeholder="0.00 to 10.00">
                    </div>
                    <button type="submit" class="btn">Commit Student Entry</button>
                </form>
            </div>
        </div>

        <div class="content-area">
            <div class="card">
                <h3>🔍 Enterprise System Dynamic Registry Lookup</h3>
                <form action="/" method="GET" class="search-box">
                    <input type="text" name="search" value="{{ search_query }}" placeholder="Type student name, email, department, university or college...">
                    <button type="submit" class="btn">Execute Search</button>
                    {% if search_query %}
                        <a href="/" class="btn" style="background-color: #95a5a6;">Reset Filter</a>
                    {% endif %}
                </form>
            </div>

            <div class="card">
                <h3>📋 Active Structural Multi-Tenant Records Matrix</h3>
                <table>
                    <thead>
                        <tr>
                            <th>UID</th>
                            <th>Student Demographics</th>
                            <th>Mapped Institution Hierarchy</th>
                            <th>Dept</th>
                            <th>CGPA</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in students %}
                        <tr>
                            <td><strong>#{{ s.student_id }}</strong></td>
                            <td>
                                <strong>{{ s.first_name }} {{ s.last_name }}</strong>
                                <br>
                                <small style="color: #555;">{{ s.email }}</small>
                            </td>
                            <td>
                                <span class="inst-badge">🏛️ {{ s.university_name or 'Independent Node' }}</span>
                                <br>
                                <span class="clg-badge">📍 {{ s.college_name or 'Unmapped Branch' }}</span>
                            </td>
                            <td><code>{{ s.department or '-' }}</code></td>
                            <td><strong>{{ s.cgpa if s.cgpa is not none else 'N/A' }}</strong></td>
                            <td>
                                <a href="/delete-student/{{ s.student_id }}" class="btn btn-danger" onclick="return confirm('Drop student configuration from infrastructure database permanently?');">Drop</a>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="6" style="text-align: center; color: #7f8c8d; padding: 40px 10px;">
                                No active cluster datasets match the requested index values. Add university nodes first!
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    search_query = request.args.get('search', '').strip()
    try:
        universities = models.get_all_universities()
        colleges = models.get_all_colleges()
        if search_query:
            students = models.search_students(search_query)
        else:
            students = models.get_all_students()
    except Exception as e:
        universities, colleges, students = [], [], []
        print(f"Error rendering index matrices: {str(e)}")
        
    return render_template_string(HTML_LAYOUT, students=students, universities=universities, colleges=colleges, search_query=search_query)

@app.route('/add-university', methods=['POST'])
def web_add_university():
    code = request.form.get('uni_code').strip().upper()
    name = request.form.get('uni_name').strip()
    try:
        models.add_university(code, name)
        flash(f"✔ University Node [{code}] registered successfully in cluster matrix!", "success")
    except Exception as e:
        flash(f"✘ Registration aborted: Entity configuration error. {str(e)}", "error")
    return redirect(url_for('home'))

@app.route('/add-college', methods=['POST'])
def web_add_college():
    uni_id = request.form.get('parent_uni_id')
    code = request.form.get('clg_code').strip().upper()
    name = request.form.get('clg_name').strip()
    try:
        models.add_college(university_id=uni_id, college_code=code, college_name=name)
        flash(f"✔ College Campus [{code}] mapped inside parent University successfully!", "success")
    except Exception as e:
        flash(f"✘ Mapping aborted: Link execution mapping exception. {str(e)}", "error")
    return redirect(url_for('home'))

@app.route('/add-student', methods=['POST'])
def web_add_student():
    first = request.form.get('first_name').strip()
    last = request.form.get('last_name').strip()
    email = request.form.get('email').strip()
    clg_id = int(request.form.get('target_college_id'))
    dept = request.form.get('department').strip()
    cgpa = request.form.get('cgpa')
    
    try:
        # Dynamic Resolution: Automatically find parent university linked to this college
        conn = models.get_db_connection()
        res = conn.execute("SELECT university_id FROM colleges WHERE college_id = ?", (clg_id,)).fetchone()
        uni_id = res[0] if res else 1
        conn.close()
        
        models.add_student(
            first_name=first, last_name=last, email=email,
            university_id=uni_id, college_id=clg_id, department=dept,
            cgpa=float(cgpa) if cgpa else None
        )
        flash("✔ Student Record synced and activated!", "success")
    except DuplicateEmailError:
        flash("✘ Integrity Error: Student email token identifier already bound.", "error")
    except Exception as e:
        flash(f"✘ Data sync exception: {str(e)}", "error")
        
    return redirect(url_for('home'))

@app.route('/delete-student/<student_id>', methods=['GET'])
def web_delete_student(student_id):
    try:
        models.delete_student(int(student_id))
        flash(f"✔ Dropped configuration link for identity target #{student_id}.", "success")
    except Exception as e:
        flash(f"✘ Dropping index fault: {str(e)}", "error")
    return redirect(url_for('home'))

port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)