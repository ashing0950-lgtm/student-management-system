import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 1. Pehle ek University confirm karo (ID 1 wali)
cursor.execute("INSERT OR IGNORE INTO universities (university_code, university_name) VALUES ('BBDU', 'BBD University')")

# 2. Ab College add karo (Ab university_id, college_code, aur name sab de rahe hain)
# Humne 'university_id' = 1 diya hai
try:
    cursor.execute("INSERT INTO colleges (university_id, college_code, college_name) VALUES (?, ?, ?)", 
                   (1, 'ENG', 'School of Engineering'))
    cursor.execute("INSERT INTO colleges (university_id, college_code, college_name) VALUES (?, ?, ?)", 
                   (1, 'MGT', 'School of Management'))
    cursor.execute("INSERT INTO colleges (university_id, college_code, college_name) VALUES (?, ?, ?)", 
                   (1, 'PHARM', 'School of Pharmacy'))
    conn.commit()
    print("Colleges successfully added!")
except sqlite3.IntegrityError as e:
    print("Error (Shayad code pehle se hai):", e)

conn.close()