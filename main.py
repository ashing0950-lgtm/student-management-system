from flask import Flask, request, redirect, url_for, render_template_string, session, flash
import models

app = Flask(__name__)
app.secret_key = 'super-secret-key-student-portal-ashish-v3'

models.init_db()

# --- AUTH LAYOUTS ---
LOGIN_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Student Portal</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .auth-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.1); width: 320px; text-align: center; }
        h2 { margin-top: 0; color: #333; }
        input { width: 93%; padding: 10px; margin: 10px 0; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; }
        .btn { width: 100%; padding: 10px; background-color: #0d6efd; color: white; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; font-weight: bold; }
        .link { display: block; margin-top: 15px; color: #6c757d; text-decoration: none; font-size: 13px; }
        .flash-msg { color: #dc3545; font-size: 13px; margin-bottom: 10px; text-align: left; }
    </style>
</head>
<body>
<div class="auth-box">
    <h2>🔑 Login</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %}<div class="flash-msg">❌ {{ msg }}</div>{% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit" class="btn">Login</button>
    </form>
    <a href="/register" class="link">Don't have an account? Register here</a>
</div>
</body>
</html>
"""

REGISTER_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>Register - Student Portal</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .auth-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.1); width: 320px; text-align: center; }
        h2 { margin-top: 0; color: #333; }
        input { width: 93%; padding: 10px; margin: 10px 0; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; }
        .btn { width: 100%; padding: 10px; background-color: #198754; color: white; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; font-weight: bold; }
        .link { display: block; margin-top: 15px; color: #6c757d; text-decoration: none; font-size: 13px; }
    </style>
</head>
<body>
<div class="auth-box">
    <h2>📝 Register</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %}
          <div class="flash-msg" style="color: #dc3545; font-size:13px; text-align:left; margin-bottom:10px;">❌ {{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST">
        <input type="text" name="username" placeholder="Choose Username" required>
        <input type="password" name="password" placeholder="Choose Password" required>
        <button type="submit" class="btn">Register Account</button>
    </form>
    <a href="/login" class="link">Already have an account? Login</a>
</div>
</body>
</html>
"""

# --- MAIN DASHBOARD LAYOUT (University Removed) ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>Student Portal</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }
        .navbar { background-color: #212529; color: white; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
        .navbar h2 { margin: 0; font-size: 18px; display: flex; align-items: center; gap: 5px; }
        .logout-btn { background-color: #dc3545; color: white; text-decoration: none; padding: 5px 10px; border-radius: 4px; font-size: 13px; font-weight: bold; }
        .container { display: flex; padding: 20px; gap: 20px; max-width: 1400px; margin: 0 auto; }
        .sidebar { width: 280px; background: white; padding: 20px; border-radius: 6px; box-shadow: 0 0 10px rgba(0,0,0,0.05); height: fit-content; }
        .sidebar h3 { margin-top: 0; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 10px; color: #333; }
        .form-group { margin-bottom: 12px; }
        .form-group input { width: 92%; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 13px; }
        .save-btn { width: 100%; padding: 10px; background-color: #198754; color: white; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; font-weight: 500; }
        .main-content { flex: 1; background: white; padding: 20px; border-radius: 6px; box-shadow: 0 0 10px rgba(0,0,0,0.05); overflow-x: auto; }
        .header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .header-section h3 { margin: 0; font-size: 18px; color: #333; }
        .search-box { display: flex; gap: 5px; align-items: center; }
        .search-box input { padding: 6px 10px; border: 1px solid #ced4da; border-radius: 4px; font-size: 13px; width: 200px; }
        .search-btn { background-color: #0d6efd; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; }
        .clear-link { color: #6c757d; text-decoration: none; font-size: 13px; margin-left: 5px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 900px; }
        th { background-color: #212529; color: white; padding: 10px; text-align: left; font-weight: 500; }
        td { padding: 10px; border-bottom: 1px solid #dee2e6; color: #333; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        .action-btns { display: flex; gap: 4px; }
        .edit-btn { background-color: #0d6efd; color: white; text-decoration: none; padding: 4px 6px; border-radius: 4px; font-size: 12px; }
        .delete-btn { background-color: #dc3545; color: white; text-decoration: none; padding: 4px 6px; border-radius: 4px; font-size: 12px; }
        .cancel-btn { display: block; text-align: center; margin-top: 10px; color: #6c757d; font-size: 13px; text-decoration: none;}
    </style>
</head>
<body>

<div class="navbar">
    <h2>🎓 Student Portal <span style="font-weight: normal; font-size: 14px; margin-left: 10px; color: #ccc;">Welcome, {{ username }}</span></h2>
    <a href="/logout" class="logout-btn">Logout</a>
</div>

<div class="container">
    <div class="sidebar">
        <h3>{% if edit_student %}✏️ Edit Student{% else %}Add New Student{% endif %}</h3>
        <form action="{% if edit_student %}/edit-student/{{ edit_student.id }}{% else %}/add-student{% endif %}" method="POST">
            <div class="form-group"><input type="text" name="full_name" placeholder="Full Name" value="{{ edit_student.full_name if edit_student else '' }}" required></div>
            <div class="form-group"><input type="email" name="email" placeholder="Email Address" value="{{ edit_student.email if edit_student else '' }}" required></div>
            <div class="form-group"><input type="number" name="age" placeholder="Age" value="{{ edit_student.age if edit_student else '' }}" required></div>
            <div class="form-group"><input type="number" step="0.01" name="cgpa" placeholder="CGPA" value="{{ edit_student.cgpa if edit_student else '' }}" required></div>
            <div class="form-group"><input type="text" name="college" placeholder="College" value="{{ edit_student.college if edit_student else '' }}" required></div>
            <div class="form-group"><input type="text" name="department" placeholder="Department" value="{{ edit_student.department if edit_student else '' }}" required></div>
            <div class="form-group"><input type="text" name="branch" placeholder="Branch" value="{{ edit_student.branch if edit_student else '' }}" required></div>
            
            <button type="submit" class="save-btn" style="background-color: {% if edit_student %}#0d6efd{% else %}#198754{% endif %};">
                {% if edit_student %}Update Student{% else %}Save Student{% endif %}
            </button>
            {% if edit_student %}
                <a href="/" class="cancel-btn">Cancel Edit</a>
            {% endif %}
        </form>
    </div>

    <div class="main-content">
        <div class="header-section">
            <h3>Registered Students Ledger</h3>
            <form action="/" method="POST" class="search-box">
                <input type="text" name="search" placeholder="Search Portal..." value="{{ search_val or '' }}">
                <button type="submit" class="search-btn">Search</button>
                {% if search_val %}
                    <a href="/" class="clear-link">Clear</a>
                {% endif %}
            </form>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 30px;">ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th style="width: 40px;">Age</th>
                    <th style="width: 45px;">CGPA</th>
                    <th>College</th>
                    <th>Department</th>
                    <th>Branch</th>
                    {% if username.lower() == 'ashish' %}<th>Added By</th>{% endif %}
                    <th style="width: 100px;">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for s in students %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td><b>{{ s.full_name }}</b></td>
                    <td>{{ s.email }}</td>
                    <td>{{ s.age }}</td>
                    <td>{{ s.cgpa }}</td>
                    <td>{{ s.college }}</td>
                    <td>{{ s.department }}</td>
                    <td>{{ s.branch }}</td>
                    {% if username.lower() == 'ashish' %}<td><span style="color:#0d6efd;">{{ s.created_by }}</span></td>{% endif %}
                    <td class="action-btns">
                        <a href="/edit-student/{{ s.id }}" class="edit-btn">Edit</a>
                        <a href="/delete-student/{{ s.id }}" class="delete-btn">Delete</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

</body>
</html>
"""

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session: return redirect(url_for('login'))
    search_val = request.form.get('search') if request.method == 'POST' else None
    students = models.get_students(session['user'], search_val)
    return render_template_string(HTML_LAYOUT, students=students, search_val=search_val, username=session['user'], edit_student=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = models.authenticate_user(username, password)
        if user:
            session['user'] = user['username']
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password")
    return render_template_string(LOGIN_LAYOUT)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if models.register_user(username, password):
            return redirect(url_for('login'))
        else:
            flash("Username already taken!")
    return render_template_string(REGISTER_LAYOUT)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add-student', methods=['POST'])
def web_add_student():
    if 'user' not in session: return redirect(url_for('login'))
    
    f_name = request.form.get('full_name')
    email = request.form.get('email')
    age = request.form.get('age')
    cgpa = request.form.get('cgpa')
    clg = request.form.get('college')
    dept = request.form.get('department')
    branch = request.form.get('branch')
    
    if f_name and email and age and cgpa:
        models.add_student(f_name, email, int(age), float(cgpa), clg, dept, branch, session['user'])
    return redirect(url_for('home'))

@app.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
def web_edit_student(student_id):
    if 'user' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        f_name = request.form.get('full_name')
        email = request.form.get('email')
        age = request.form.get('age')
        cgpa = request.form.get('cgpa')
        clg = request.form.get('college')
        dept = request.form.get('department')
        branch = request.form.get('branch')
        
        if f_name and email and age and cgpa:
            models.update_student(student_id, f_name, email, int(age), float(cgpa), clg, dept, branch)
        return redirect(url_for('home'))
    
    student = models.get_student_by_id(student_id)
    students = models.get_students(session['user'])
    return render_template_string(HTML_LAYOUT, students=students, search_val=None, username=session['user'], edit_student=student)

@app.route('/delete-student/<int:student_id>')
def web_delete_student(student_id):
    if 'user' not in session: return redirect(url_for('login'))
    models.delete_student(student_id)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)