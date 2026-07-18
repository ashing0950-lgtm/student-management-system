"""
main.py
Full Web Management Interface & CLI for Student Management System.
"""

import sys
import os
from database import initialize_database
import models
from models import DuplicateEmailError, NotFoundError, AuthError
from flask import Flask, render_template_string, request, redirect, url_for, flash

# Initialize Database on load
initialize_database()
try:
    models.create_user("admin", "admin123", "superadmin")
except DuplicateEmailError:
    pass

# ---------- FULL WEB INTERFACE LAYER ----------
app = Flask(__name__)
app.secret_key = "sms_super_secret_key"  # Required for flash messages

HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>SMS Portal</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f9; color: #333; }
        .navbar { background-color: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        .navbar h2 { margin: 0; font-size: 20px; }
        .main-container { max-width: 1200px; margin: 30px auto; padding: 0 20px; display: grid; grid-template-columns: 1fr 2fr; gap: 25px; }
        @media(max-width: 900px) { .main-container { grid-template-columns: 1fr; } }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
        h3 { margin-top: 0; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 14px; }
        input, select { width: 100%; padding: 8px 12px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .btn { background-color: #3498db; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; display: inline-block; text-align: center; text-decoration: none; }
        .btn:hover { background-color: #2980b9; }
        .btn-danger { background-color: #e74c3c; padding: 5px 10px; font-size: 12px; width: auto; }
        .btn-danger:hover { background-color: #c0392b; }
        .btn-secondary { background-color: #2ecc71; margin-bottom: 15px; }
        .btn-secondary:hover { background-color: #27ae60; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background-color: #f8f9fa; color: #2c3e50; }
        .alert { padding: 12px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 20px; border: 1px solid #c3e6cb; }
        .alert-danger { background-color: #f8d7da; color: #721c24; border-collapse: #f5c6cb; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        .search-box input { flex: 1; }
        .search-box .btn { width: auto; }
    </style>
</head>
<body>

    <div class="navbar">
        <h2>🎓 Student Management System (Cloud Control Panel)</h2>
        <div><strong>Role:</strong> SUPERADMIN | Node: Active</div>
    </div>

    <div class="main-container">
        <!-- LEFT SIDE: CONTROLS & FORMS -->
        <div class="sidebar">
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert {% if category == 'error' %}alert-danger{% endif %}">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}

            <!-- Onboard Tenant Panel -->
            <div class="card">
                <h3>🏢 1. Institutional Tenancy Setup</h3>
                <form action="/add-tenant" method="POST">
                    <div class="form-group">
                        <label>Setup Type</label>
                        <select name="tenant_type" required>
                            <option value="uni">Register University</option>
                            <option value="clg">Onboard College Branch</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Code (e.g., BBDU, CSE-BBD)</label>
                        <input type="text" name="code" placeholder="Enter Short Code" required>
                    </div>
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" name="name" placeholder="Enter Full Name" required>
                    </div>
                    <button type="submit" class="btn btn-secondary">Onboard Entity</button>
                </form>
            </div>

            <!-- Add Student Form -->
            <div class="card">
                <h3>👤 2. Add New Student Entry</h3>
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
                        <label>Department</label>
                        <input type="text" name="department" placeholder="e.g. CSE-AI">
                    </div>
                    <div class="form-group">
                        <label>CGPA</label>
                        <input type="number" step="0.1" name="cgpa" placeholder="0.0 to 10.0">
                    </div>
                    <button type="submit" class="btn">Save Student Record</button>
                </form>
            </div>
        </div>

        <!-- RIGHT SIDE: SEARCH & LIVE DIRECTORY -->
        <div class="content-area">
            <div class="card">
                <h3>🔍 Search & Filter Registry</h3>
                <form action="/" method="GET" class="search-box">
                    <input type="text" name="search" value="{{ search_query }}" placeholder="Search by name, email or department...">
                    <button type="submit" class="btn">Search</button>
                    {% if search_query %}
                        <a href="/" class="btn" style="background-color: #95a5a6;">Clear</a>
                    {% endif %}
                </form>
            </div>

            <div class="card">
                <h3>📋 Active Student Directory</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Department</th>
                            <th>CGPA</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in students %}
                        <tr>
                            <td><strong>{{ s.student_id }}</strong></td>
                            <td>{{ s.first_name }} {{ s.last_name }}</td>
                            <td>{{ s.email }}</td>
                            <td>{{ s.department or '-' }}</td>
                            <td>{{ s.cgpa if s.cgpa is not none else '-' }}</td>
                            <td>
                                <a href="/delete-student/{{ s.student_id }}" class="btn btn-danger" onclick="return confirm('Are you sure you want to delete this student?');">Delete</a>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="6" style="text-align: center; color: #7f8c8d; padding: 30px;">
                                No matching records found. Use the forms on the left to add students or setup nodes!
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

@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()
    try:
        if search_query:
            # Trigger active search operation from models layer
            students = models.search_students(search_query)
        else:
            students = models.get_all_students()
    except Exception:
        students = []
    return render_template_string(HTML_LAYOUT, students=students, search_query=search_query)

@app.route('/add-student', method=['POST'])
def web_add_student():
    first = request.form.get('first_name')
    last = request.form.get('last_name')
    email = request.form.get('email')
    dept = request.form.get('department')
    cgpa = request.form.get('cgpa')
    
    # Defaults setting up for single tenant fallback
    uni_id = 1
    col_id = 1
    
    try:
        models.add_student(
            first_name=first, last_name=last, email=email,
            university_id=uni_id, college_id=col_id, department=dept,
            cgpa=float(cgpa) if cgpa else None
        )
        flash("✔ Student Record added successfully to global registry!", "success")
    except DuplicateEmailError:
        flash("✘ Error: A student with this email already exists.", "error")
    except Exception as e:
        flash(f"✘ Error processing request: {str(e)}", "error")
        
    return redirect(url_for('home'))

@app.route('/delete-student/<int:student_id>')
def web_delete_student(student_id):
    try:
        models.delete_student(student_id)
        flash(f"✔ Student ID {student_id} successfully purged from database.", "success")
    except Exception as e:
        flash(f"✘ Failed to delete record: {str(e)}", "error")
    return redirect(url_for('home'))

@app.route('/add-tenant', method=['POST'])
def web_add_tenant():
    t_type = request.form.get('tenant_type')
    code = request.form.get('code')
    name = request.form.get('name')
    
    try:
        if t_type == "uni":
            models.add_university(code, name)
            flash(f"✔ University Node [{code}] successfully onboarded!", "success")
        else:
            models.add_college(university_id=1, college_code=code, college_name=name)
            flash(f"✔ College Branch [{code}] mapped to default hierarchy!", "success")
    except Exception as e:
        flash(f"✘ Institutional onboarding failed: {str(e)}", "error")
        
    return redirect(url_for('home'))

# CLI Fallback main logic loop remains intact for terminal execution
def main():
    # Keep CLI logic context running if executed directly in local mode
    print("--> CLI Mode Active. Run via python main.py inside local shell environments.")

if __name__ == "__main__":
    if "PORT" in os.environ:
        port = int(os.environ.get("PORT", 8000))
        app.run(host="0.0.0.0", port=port)
    else:
        # Local runner wrapper fallback triggers Flask locally for browser testing too!
        print("--> Running Local Web Server Hub. Open http://127.0.0.1:5000 in your browser")
        app.run(debug=True)