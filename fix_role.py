import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
# 'Ashish' username wale ka role update karo
cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'Ashish'")
conn.commit()
print("Role update ho gaya! Ab admin login try karo.")
conn.close()