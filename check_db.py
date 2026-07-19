import sqlite3

def check_users():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        users = cursor.execute("SELECT * FROM users").fetchall()
        print("--- Database Users ---")
        for u in users:
            print(f"ID: {u[0]}, Username: {u[1]}, Role: {u[3]}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    check_users()