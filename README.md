# Student Management System

A simple command-line Student Management System built with Python and SQLite
(no external dependencies — uses only the standard library).

## Features

- **Login/Logout:** username & password sign-in before any menu is shown;
  passwords are salted and hashed (PBKDF2-HMAC-SHA256), never stored in
  plain text
- **User management:** change your own password; add/list/delete user
  accounts from the "Manage users" menu
- **Students:** add, list, search, update, delete, full profile view
  (phone, address, department, enrollment year, CGPA)
- **Bulk CSV import:** load thousands of student records at once with
  `import_csv.py`
- **Courses:** add, list, delete
- **Enrollment:** enroll students in courses, assign/update grades
- **Reports:** view a student's transcript, view a course roster
- Data is persisted in a local SQLite database file (`school.db`), created
  automatically on first run

## Importing Students from a CSV File

If you have student data in a CSV file, you can bulk-load it without
typing anything manually. The importer expects these column headers
(case-sensitive):

```
StudentID, FirstName, LastName, DateOfBirth, Email, Phone, Address,
Department, EnrollmentYear, CGPA
```

Run:

```bash
python import_csv.py path/to/your_file.csv
```

The script will:
- Skip rows missing a name or email, and report them
- Skip rows whose email or StudentID already exists in the database
  (nothing gets overwritten) and list the first 10 skipped rows
- Print a summary: how many were inserted vs. skipped

`StudentID` values from the CSV (e.g. `S00001`) are kept as a separate
"external ID" field so they don't clash with the database's own internal
auto-incrementing ID — both are shown wherever a student is displayed.

## Signing In

On first run, a default account is created automatically:

```
Username: admin
Password: admin123
```

**Change this password right away** using menu option 13 ("Change my
password") after your first login. From the login screen, type `exit`
as the username at any time to quit without signing in.

## Requirements

- Python 3.7+
- No third-party packages needed

## How to Run

```bash
python main.py
```

You'll see a numbered menu. Enter a number to perform an action, then
follow the prompts.

## Project Structure

```
student_management_system/
├── main.py        # CLI menu, login screen, and user interaction
├── models.py      # CRUD + auth functions (business logic / data access)
├── database.py    # SQLite connection + schema setup (incl. users table)
├── auth.py        # Password hashing (stdlib-only, PBKDF2-HMAC-SHA256)
├── import_csv.py  # Bulk-import students from a CSV file
├── school.db      # Created automatically on first run
└── README.md
```

## Example Workflow

1. Log in with `admin` / `admin123`
2. Choose `13` to set your own password
3. Choose `1` to add a student (e.g. Alice Nguyen, alice@example.com)
4. Choose `6` to add a course (e.g. CS101, Intro to Computer Science)
5. Choose `9` to enroll the student in the course
6. Choose `10` to set a grade
7. Choose `11` to view the student's transcript
8. Choose `15` to log out, or `0` to exit the program entirely

## Extending the Project

Some natural next steps if you want to build on this:

- Add attendance tracking
- Add a GPA calculator (weight grades by credits)
- Export transcripts to PDF or CSV
- Wrap `models.py` in a web interface (e.g. Flask/FastAPI)
- Add user authentication for admin vs. student roles

## Notes on Design

- All database logic lives in `models.py`, so the CLI (`main.py`) never
  writes raw SQL — this makes it easy to later swap in a web UI or REST
  API without touching the data layer.
- Foreign keys and `UNIQUE` constraints (e.g. one email per student, one
  enrollment per student/course pair) are enforced at the database level.
- Custom exceptions (`DuplicateEmailError`, `NotFoundError`, `AuthError`)
  make error handling explicit and easy to catch in any interface layer.
- Passwords are hashed with a random per-user salt (see `auth.py`) using
  only the Python standard library — no extra dependency to install.
