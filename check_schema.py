import sqlite3
try:
    conn = sqlite3.connect('socializer.sqlite')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(metrics)")
    print(cursor.fetchall())
    conn.close()
except Exception as e:
    print(e)
