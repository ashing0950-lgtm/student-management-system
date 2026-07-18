import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 1. Pehle ek University add karo (Kyunki college ke liye university_id zaroori hai)
cursor.execute("INSERT OR IGNORE INTO universities (university_code, university_name) VALUES ('BBDU', 'BBD University')")

# 2. Ab College add karo (Ab university_id: 1 ka use karenge)
# Hum 1st university_id (BBDU) ke under college daal rahe hain
cursor.execute("INSERT INTO colleges (university_id, college_code, college_name) VALUES (?, ?, ?)", 
               (1, 'ENG01', 'School of Engineering'))
cursor.execute("INSERT INTO colleges (university_id, college_code, college_name) VALUES (?, ?, ?)", 
               (1, 'MGT01', 'School of Management'))

conn.commit()
conn.close()
print("University aur Colleges successfully add ho gaye!")