import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import models

app = Flask(__name__)
app.secret_key = "super_secret_key"

# --- LOGIN PAGE HTML ---
LOGIN_LAYOUT = """
<h2>Login</h2>
<form method="POST">
    <input type="text" name="username" placeholder="Username" required><br>
    <input type="password" name="password" placeholder="Password" required><br>
    <button type="submit">Login</button>
</form>
"""

REGISTER_LAYOUT = """
<h2>Register New User</h2>
<form method="POST">
    <input type="text" name="username" placeholder="Username" required><br>
    <input type="password" name="password" placeholder="Password" required><br>
    <select name="role">
        <option value="user">User</option>
        <option value="admin">Admin</option>
    </select><br>
    <button type="submit">Create Account</button>
</form>
<br><a href="/">Back to Home</a>
"""

# --- MAIN DASHBOARD HTML ---
HTML_LAYOUT = """
<style>
    body { font-family: sans-serif; padding: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
    .form-box { background: #f4f4f4; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .btn { padding: 8px 12px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
</style>

<h1>Student Management System</h1>
<p>Logged in as: {{ current_user.username }} | <a href="/logout">Logout</a></p>

<!-- Navigation Links -->
<div style="margin-bottom: 20px;">
    <a href="/" class="btn">🏠 Home</a>
    {% if current_user.role == 'admin' %}
        <a href="/register-user" class="btn" style="background:#28a745;">➕ Register New User</a>
    {% endif %}
</div>

<div class="form-box">
    <h3>🔍 Search Students</h3>
    <form action="/" method="GET" style="display:flex; gap:10px;">
        <input type="text" name="search" placeholder="Search by name or dept...">
        <button type="submit">Search</button>
        <a href="/">Clear</a>
    </form>
</div>

<div class="form-box">
    <h2>Register Student</h2>
    <form action="/add-student" method="POST">
        <input type="text" name="first_name" placeholder="First Name" required>
        <input type="text" name="last_name" placeholder="Last Name" required>
        <input type="email" name="email" placeholder="Email" required>
        
        <select name="college_id" required>
            <option value="">-- Select College --</option>
            {% for c in colleges %}
                <option value="{{ c.college_id }}">{{ c.college_name }}</option>
            {% endfor %}
        </select>
        
        <input type="text" name="department" placeholder="Department" required>
        <input type="number" step="0.01" name="cgpa" placeholder="CGPA">
        <button type="submit">Commit Student Entry</button>
    </form>
</div>

<h2>Active Student Records</h2>
<table>
    <tr><th>Name</th><th>College</th><th>Dept</th><th>CGPA</th><th>Actions</th></tr>
    {% for s in students %}
    <tr>
        <td>{{ s.first_name }} {{ s.last_name }}</td>
        <td>{{ s.college_name }}</td>
        <td>{{ s.department }}</td>
        <td>{{ s.cgpa }}</td>
        <td>
            <a href="/edit-student/{{ s.student_id }}">Edit</a> | 
            <a href="/delete-student/{{ s.student_id }}" style="color:red;">Drop</a>
        </td>
    </tr>
    {% endfor %}
</table>
"""

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = models.authenticate_user(request.form.get('username'), request.form.get('password'))
        if user:
            session['user'] = user
            return redirect(url_for('home'))
        flash("Invalid Login!")
    return render_template_string(LOGIN_LAYOUT)

@app.route('/', methods=['GET'])
def home():
    if 'user' not in session: return redirect(url_for('login'))
    
    # Data Fetching
    students = models.get_students_by_role(session['user'])
    colleges = models.get_all_colleges()
    
    return render_template_string(HTML_LAYOUT, students=students, colleges=colleges, current_user=session['user'])

@app.route('/add-student', methods=['POST'])
def web_add_student():
    if 'user' not in session: return redirect(url_for('login'))
    
    clg_id = request.form.get('college_id')
    models.add_student(
        first_name=request.form.get('first_name'),
        last_name=request.form.get('last_name'),
        email=request.form.get('email'),
        department=request.form.get('department'),
        college_id=int(clg_id),
        cgpa=float(request.form.get('cgpa') or 0),
        created_by=session['user']['user_id']
    )
    return redirect(url_for('home'))

@app.route('/delete-student/<int:student_id>')
def delete(student_id):
    if 'user' not in session: return redirect(url_for('login'))
    models.delete_student(student_id)
    return redirect(url_for('home'))

@app.route('/register-user', methods=['GET', 'POST'])
def register_user():
    # Sirf admin hi naye user bana sakta hai
    if 'user' not in session or session['user']['role'] != 'admin':
        return "Access Denied!", 403
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        models.add_user(username, password, role)
        flash("User created successfully!")
        return redirect(url_for('home'))
        
    return render_template_string(REGISTER_LAYOUT)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=8000)