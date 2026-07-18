import sqlite3

conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# 1. Sabhi records ko 'admin' (ID 1) se link kar dete hain agar wo 0 hain
cursor.execute("UPDATE students SET created_by = 1 WHERE created_by = 0 OR created_by IS NULL")
conn.commit()

# 2. Check karte hain ki ab status kya hai
rows = cursor.execute("SELECT student_id, first_name, created_by FROM students").fetchall()
for row in rows:
    print(f"Student ID: {row[0]} | Name: {row[1]} | Linked to UserID: {row[2]}")

conn.close()
print("\n[Done] Migration complete! Purane records ab Admin (ID 1) ke naam ho gaye hain.")