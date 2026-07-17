"""
main.py
Hybrid Command-line interface & Web Server wrapper for Student Management System.
"""

import sys
import os
from database import initialize_database  # database.py ke function ke sath map kiya
import models
from models import DuplicateEmailError, NotFoundError, AuthError
from flask import Flask, render_template_string

# Global Active Session Scope Boundaries
current_user = None  
active_university_id = None
active_college_id = None

# ---------- WEB SERVER INSTANCE FOR CLOUD DEPLOYMENT ----------
app = Flask(__name__)

# Ek clean aur modern HTML dashboard template browser view ke liye
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Student Management System</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background-color: #f5f7fb; color: #333; }
        .container { max-width: 950px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1 { color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; margin-bottom: 5px; }
        .status-badge { background-color: #2ecc71; color: white; padding: 6px 14px; border-radius: 20px; font-size: 13px; display: inline-block; margin-bottom: 25px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background-color: #f8f9fa; color: #2c3e50; font-weight: 600; text-transform: uppercase; font-size: 13px; }
        tr:hover { background-color: #fdfdfd; }
        .no-data { text-align: center; color: #7f8c8d; padding: 40px; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Student Management System Dashboard</h1>
        <div class="status-badge">● Live Cloud Sync Active</div>
        
        <h3>Registered Students (Global Directory View)</h3>
        <table>
            <thead>
                <tr>
                    <th>Internal ID</th>
                    <th>Full Name</th>
                    <th>Email Address</th>
                    <th>Department</th>
                    <th>CGPA</th>
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
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" class="no-data">No student records found in the system registry. Connect your local CLI node or import rows via Option 17 to view data here!</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # Jaise hi cloud link open hogi, ye direct database se data nikal kar template me bhejega
    try:
        # Purane records live loading ke liye helper database method call
        all_students = models.get_all_students()
    except Exception:
        all_students = []
    return render_template_string(HTML_TEMPLATE, students=all_students)


def pause():
    input("\nPress Enter to continue...")


def print_header(title):
    print("\n" + "=" * 50)
    print(title.center(50))
    print("=" * 50)


def print_students(students):
    if not students:
        print("No students found.")
        return
    print(f"{'ID':<6}{'Name':<22}{'Email':<28}{'Dept':<14}{'CGPA':<6}")
    print("-" * 76)
    for s in students:
        name = f"{s['first_name']} {s['last_name']}"
        sid = s.get('external_id') or s['student_id']
        cgpa = s.get('cgpa')
        print(f"{str(sid):<6}{name:<22}{s['email']:<28}{s.get('department') or '-':<14}{cgpa if cgpa is not None else '-':<6}")


def print_courses(courses):
    if not courses:
        print("No courses found.")
        return
    print(f"{'ID':<4}{'Code':<10}{'Name':<30}{'Credits':<8}")
    print("-" * 52)
    for c in courses:
        print(f"{c['course_id']:<4}{c['course_code']:<10}{c['course_name']:<30}{c['credits']:<8}")


# ---------- AUTH SCREENS ----------

def login_screen():
    """Loop until the user logs in successfully or chooses to exit."""
    global active_university_id, active_college_id
    print_header("STUDENT MANAGEMENT SYSTEM — Sign In")
    print("Default account -> username: admin | password: admin123")
    print("(Type 'exit' as the username at any time to quit)\n")

    while True:
        username = input("Username: ").strip()
        if username.lower() == "exit":
            return None
        password = input("Password: ").strip()
        user = models.verify_login(username, password)
        if user:
            print(f"\n✔ Welcome, {user['username']} ({user['role'].upper()}).")
            active_university_id = user.get("university_id")
            active_college_id = user.get("college_id")
            return user
        print("\n✘ Invalid username or password. Please try again.\n")


def action_change_password():
    print_header("Change Password")
    current = input("Current password: ").strip()
    new = input("New password (min 6 characters): ").strip()
    confirm = input("Confirm new password: ").strip()

    if len(new) < 6:
        print("\n✘ Error: new password must be at least 6 characters.")
        return
    if new != confirm:
        print("\n✘ Error: passwords do not match.")
        return
    try:
        models.change_password(current_user["username"], current, new)
        print("\n✔ Password updated successfully.")
    except AuthError as e:
        print(f"\n✘ Error: {e}")


def action_manage_users():
    print_header("Manage Users (admin only)")
    if current_user["role"] not in ["admin", "superadmin"]:
        print("\n✘ Access Denied: Requires administrative clearances.")
        return

    print("1. List users")
    print("2. Add user")
    print("3. Delete user")
    choice = input("Select an option: ").strip()

    if choice == "1":
        users = models.get_all_users(university_id=active_university_id)
        print(f"\n{'ID':<4}{'Username':<20}{'Role':<10}{'Created on':<20}")
        print("-" * 54)
        for u in users:
            print(f"{u['user_id']:<4}{u['username']:<20}{u['role']:<10}{u['created_on']:<20}")
    elif choice == "2":
        username = input("New username: ").strip()
        password = input("New password (min 6 characters): ").strip()
        role = input("Role [admin]: ").strip() or "admin"
        if len(password) < 6:
            print("\n✘ Error: password must be at least 6 characters.")
            return
        try:
            models.create_user(username, password, role, university_id=active_university_id, college_id=active_college_id)
            print(f"\n✔ User '{username}' created inside your tenant branch.")
        except DuplicateEmailError as e:
            print(f"\n✘ Error: {e}")
    elif choice == "3":
        username = input("Username to delete: ").strip()
        if username == current_user["username"]:
            print("\n✘ Error: you cannot delete the account you're logged in as.")
            return
        try:
            models.delete_user(username)
            print(f"\n✔ User '{username}' deleted.")
        except NotFoundError as e:
            print(f"\n✘ Error: {e}")


class LogoutSignal(Exception):
    pass


def action_logout():
    confirm = input("Are you sure you want to log out? (y/n): ").strip().lower()
    if confirm == "y":
        raise LogoutSignal()


def action_manage_tenants():
    print_header("Tenancy Configuration Panel")
    if current_user["role"] not in ["superadmin", "admin"]:
        print("\n✘ Access Denied: High level system operator rights required.")
        return
        
    print("1. Register a New University Entity")
    print("2. Onboard a New College Branch")
    choice = input("Select an option: ").strip()

    if choice == "1":
        code = input("Enter University Code (e.g., BBDU): ").strip()
        name = input("Enter Full University Name: ").strip()
        try:
            models.add_university(code, name)
            print("\n✔ University database node successfully initialized.")
        except Exception as e:
            print(f"\n✘ Error: {e}")
    elif choice == "2":
        unis = models.get_all_universities()
        if not list(unis):
            print("\n✘ Error: No parent universities available. Onboard one first.")
            return
        print("\nActive Universities:")
        for u in unis:
            print(f"  [{u['university_id']}] {u['university_code']} - {u['university_name']}")
        
        try:
            uid = int(input("\nSelect Parent University ID: ").strip())
            code = input("Enter College Code (e.g., CSE-BBD): ").strip()
            name = input("Enter College Branch Name: ").strip()
            models.add_college(uid, code, name)
            print("\n✔ College branch successfully bound to parent university registry.")
        except Exception as e:
            print(f"\n✘ Error: {e}")


def action_bulk_text_import():
    print_header("Raw Text Area Bulk Student Import")
    uni_id = active_university_id
    col_id = active_college_id

    if not uni_id:
        unis = models.get_all_universities()
        if not unis:
            print("\n✘ System Setup Required: Register a University before importing records.")
            return
        print("\nAvailable Destination Universities:")
        for u in unis:
            print(f"  [{u['university_id']}] {u['university_code']}")
        try:
            uni_id = int(input("\nSelect Destination University ID: ").strip())
        except ValueError:
            print("\n✘ Error: Invalid integer ID.")
            return

    if not col_id:
        colleges = models.get_colleges_by_university(uni_id)
        if not colleges:
            print("\n✘ System Setup Required: Onboard a College under this University first.")
            return
        print("\nAvailable Destination Colleges:")
        for c in colleges:
            print(f"  [{c['college_id']}] {c['college_code']}")
        try:
            col_id = int(input("\nSelect Destination College ID: ").strip())
        except ValueError:
            print("\n✘ Error: Invalid integer ID.")
            return

    print("\nInstructions:")
    print("Paste your flat student rows block below. Columns format structure:")
    print("  First_Name, Last_Name, Email, Department, CGPA")
    print("Example Data Row:\n  Ashish, Singh, ashish@bbdu.ac.in, CSE-AI, 9.5")
    print("\n[Action] Paste records now. When completed, press Enter on a blank line,")
    print("         type 'SAVE' and hit Enter once more to commit.")
    print("-" * 60)

    raw_lines = []
    while True:
        line = input()
        if line.strip().upper() == "SAVE":
            break
        if line.strip():
            raw_lines.append(line.strip())

    if not raw_lines:
        print("\n[Cancelled] Data text payload buffer was empty.")
        return

    parsed_records = []
    for idx, row in enumerate(raw_lines):
        tokens = [t.strip() for t in row.replace('\t', ',').split(',')]
        if len(tokens) >= 3:
            parsed_records.append({
                "first_name": tokens[0],
                "last_name": tokens[1],
                "email": tokens[2],
                "department": tokens[3] if len(tokens) > 3 else "General",
                "cgpa": float(tokens[4]) if len(tokens) > 4 else 0.0,
                "university_id": uni_id,
                "college_id": col_id
            })
        else:
            print(f"  -> [Line Skipping Warning] Row {idx+1} layout corrupted: '{row}'")

    print(f"\nProcessing insertion pipeline for {len(parsed_records)} data rows...")
    inserted, skipped = models.bulk_import_students(parsed_records, uni_id, col_id)

    print(f"\n✔ Complete: Added {inserted} records successfully to database instance.")
    if skipped:
        print(f"⚠ Warning: Skipped {len(skipped)} lines due to integrity conflicts (Duplicate Emails).")
        for rec, err in skipped[:3]:
            print(f"    Failed Profile email: {rec['email']} | Reason: {err}")


def action_view_student_details():
    print_header("Student Details")
    try:
        sid = int(input("Student ID (internal): ").strip())
        s = models.get_student(sid)
    except (ValueError, NotFoundError) as e:
        print(f"\n✘ Error: {e}")
        return

    print(f"\nInternal ID:     {s['student_id']}")
    print(f"External ID:     {s.get('external_id') or '-'}")
    print(f"Name:            {s['first_name']} {s['last_name']}")
    print(f"Email:           {s['email']}")
    print(f"Phone:           {s.get('phone') or '-'}")
    print(f"Date of birth:   {s.get('date_of_birth') or '-'}")
    print(f"Address:         {s.get('address') or '-'}")
    print(f"Department:      {s.get('department') or '-'}")
    print(f"Enrollment year: {s.get('enrollment_year') or '-'}")
    print(f"CGPA:            {s.get('cgpa') if s.get('cgpa') is not None else '-'}")


def action_add_student():
    print_header("Add New Student")
    first = input("First name: ").strip()
    last = input("Last name: ").strip()
    email = input("Email: ").strip()
    dob = input("Date of birth (YYYY-MM-DD, optional): ").strip() or None
    phone = input("Phone (optional): ").strip() or None
    address = input("Address (optional): ").strip() or None
    department = input("Department (optional): ").strip() or None
    enrollment_year = input("Enrollment year (optional): ").strip() or None
    cgpa = input("CGPA (optional): ").strip() or None
    
    uni_id = active_university_id
    col_id = active_college_id
    
    if not uni_id or not col_id:
        print("\n✘ Error: Standalone admins must utilize Option 17 (Bulk Text Import Area)")
        print("or select structural keys manually inside data access fields.")
        return

    try:
        sid = models.add_student(
            first, last, email, university_id=uni_id, college_id=col_id,
            date_of_birth=dob, phone=phone, address=address, department=department,
            enrollment_year=int(enrollment_year) if enrollment_year else None,
            cgpa=float(cgpa) if cgpa else None,
        )
        print(f"\n✔ Student added with ID {sid}.")
    except DuplicateEmailError as e:
        print(f"\n✘ Error: {e}")
    except ValueError:
        print("\n✘ Error: enrollment year and CGPA must be numbers.")


def action_list_students():
    print_header("All Students (Tenancy Context Enforced)")
    students = models.get_all_students(university_id=active_university_id, college_id=active_college_id)
    print_students(students)


def action_search_students():
    print_header("Search Students")
    keyword = input("Enter name or email keyword: ").strip()
    print_students(models.search_students(keyword, university_id=active_university_id))


def action_update_student():
    print_header("Update Student")
    try:
        sid = int(input("Student ID to update: ").strip())
        student = models.get_student(sid)
    except (ValueError, NotFoundError) as e:
        print(f"\n✘ Error: {e}")
        return

    print(f"Leave blank to keep current value.")
    first = input(f"First name [{student['first_name']}]: ").strip() or student['first_name']
    last = input(f"Last name [{student['last_name']}]: ").strip() or student['last_name']
    email = input(f"Email [{student['email']}]: ").strip() or student['email']
    dob = input(f"Date of birth [{student['date_of_birth'] or '-'}]: ").strip() or student['date_of_birth']

    try:
        models.update_student(sid, first_name=first, last_name=last, email=email, date_of_birth=dob)
        print("\n✔ Student updated.")
    except (DuplicateEmailError, NotFoundError) as e:
        print(f"\n✘ Error: {e}")


def action_delete_student():
    print_header("Delete Student")
    try:
        sid = int(input("Student ID to delete: ").strip())
        models.delete_student(sid)
        print("\n✔ Student deleted.")
    except (ValueError, NotFoundError) as e:
        print(f"\n✘ Error: {e}")


def action_add_course():
    print_header("Add New Course")
    code = input("Course code (e.g. CS101): ").strip()
    name = input("Course name: ").strip()
    try:
        credits = int(input("Credits [3]: ").strip() or 3)
        cid = models.add_course(code, name, credits)
        print(f"\n✔ Course added with ID {cid}.")
    except (ValueError, DuplicateEmailError) as e:
        print(f"\n✘ Error: {e}")


def action_list_courses():
    print_header("All Courses")
    print_courses(models.get_all_courses())


def action_delete_course():
    print_header("Delete Course")
    try:
        cid = int(input("Course ID to delete: ").strip())
        models.delete_course(cid)
        print("\n✔ Course deleted.")
    except (ValueError, NotFoundError) as e:
        print(f"\n✘ Error: {e}")


def action_enroll_student():
    print_header("Enroll Student in Course")
    try:
        sid = int(input("Student ID: ").strip())
        cid = int(input("Course ID: ").strip())
        models.enroll_student(sid, cid)
        print("\n✔ Enrollment successful.")
    except (ValueError, NotFoundError, DuplicateEmailError) as e:
        print(f"\n✘ Error: {e}")


def action_set_grade():
    print_header("Set / Update Grade")
    try:
        sid = int(input("Student ID: ").strip())
        cid = int(input("Course ID: ").strip())
        grade = input("Grade (e.g. A, B+, 92): ").strip()
        models.set_grade(sid, cid, grade)
        print("\n✔ Grade recorded.")
    except (ValueError, NotFoundError) as e:
        print(f"\n✘ Error: {e}")


def action_view_transcript():
    print_header("Student Transcript")
    try:
        sid = int(input("Student ID: ").strip())
        student = models.get_student(sid)
        rows = models.get_student_transcript(sid)
        print(f"\nTranscript for {student['first_name']} {student['last_name']} (ID {sid})")
        if not rows:
            print("No enrollments yet.")
        else:
            print(f"{'Code':<10}{'Course':<30}{'Credits':<9}{'Grade':<6}")
            print("-" * 55)
            for r in rows:
                print(f"{r['course_code']:<10}{r['course_name']:<30}{r['credits']:<9}{r['grade'] or '-':<6}")
    except (ValueError, NotFoundError) as e:
        print(f"\n✘ Error: {e}")


def action_view_roster():
    print_header("Course Roster")
    try:
        cid = int(input("Course ID: ").strip())
        rows = models.get_course_roster(cid)
        if not rows:
            print("No students enrolled.")
        else:
            print(f"{'ID':<4}{'Name':<25}{'Email':<28}{'Grade':<6}")
            print("-" * 63)
            for r in rows:
                name = f"{r['first_name']} {r['last_name']}"
                print(f"{r['student_id']:<4}{name:<25}{r['email']:<28}{r['grade'] or '-':<6}")
    except ValueError as e:
        print(f"\n✘ Error: {e}")


def build_menu_text():
    return f"""
STUDENT MANAGEMENT SYSTEM   (logged in as: {current_user['username']} · {current_user['role'].upper()})
--------------------------------
 1. Add student (Single entry)
 2. List all students (Isolated)
 3. Search students
 4. Update student
 5. Delete student
 6. View student details (full profile)
--------------------------------
 7. Add course
 8. List all courses
 9. Delete course
--------------------------------
10. Enroll student in course
11. Set/update grade
12. View student transcript
13. View course roster
--------------------------------
14. Change my password
15. Manage users (admin)
16. Log out
--------------------------------
NEW EXTENSIONS LAYER:
17. Paste Raw Bulk Text Data Area Import
18. Manage Institutional Tenant Framework Nodes
--------------------------------
 0. Exit program
"""


ACTIONS = {
    "1": action_add_student,
    "2": action_list_students,
    "3": action_search_students,
    "4": action_update_student,
    "5": action_delete_student,
    "6": action_view_student_details,
    "7": action_add_course,
    "8": action_list_courses,
    "9": action_delete_course,
    "10": action_enroll_student,
    "11": action_set_grade,
    "12": action_view_transcript,
    "13": action_view_roster,
    "14": action_change_password,
    "15": action_manage_users,
    "16": action_logout,
    "17": action_bulk_text_import,
    "18": action_manage_tenants,
}


def run_session():
    while True:
        print(build_menu_text())
        choice = input("Select an option: ").strip()
        if choice == "0":
            print("\nGoodbye!")
            raise SystemExit
        action = ACTIONS.get(choice)
        if action:
            action()
            pause()
        else:
            print("\nInvalid option, please try again.")


def main():
    global current_user
    initialize_database()

    try:
        models.create_user("admin", "admin123", "superadmin")
    except DuplicateEmailError:
        pass

    while True:
        current_user = login_screen()
        if current_user is None:
            print("\nGoodbye!")
            return
        try:
            run_session()
        except LogoutSignal:
            current_user = None
            print("\nYou have been logged out.\n")
            continue


# ---------- HYBRID EXECUTION ENVIRONMENT CHECK ----------
if __name__ == "__main__":
    # Agar application Render Cloud Server par chal rahi hai
    if "PORT" in os.environ:
        print("--> Cloud Environment Detected. Starting Dynamic Web Dashboard...")
        port = int(os.environ.get("PORT", 8000))
        app.run(host="0.0.0.0", port=port)
    else:
        # Agar local computer par chala rahe ho
        print("--> Local Terminal Environment Detected. Starting CLI...")
        main()