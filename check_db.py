import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Naye colleges add kar rahe hain
colleges_list = [
    ('School of Engineering (CSE)',),
    ('School of Management (MBA)',),
    ('School of Computer Applications (BCA)',),
    ('School of Pharmacy',)
]

cursor.executemany("INSERT OR IGNORE INTO colleges (college_name) VALUES (?)", colleges_list)

conn.commit()
conn.close()
print("Naye Colleges add ho gaye hain!")