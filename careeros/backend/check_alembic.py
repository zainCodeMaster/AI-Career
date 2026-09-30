import sqlite3
conn = sqlite3.connect('careeros.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
result = cursor.fetchone()
if result:
    cursor.execute('SELECT * FROM alembic_version')
    print('Current revision:', cursor.fetchall())
else:
    print('alembic_version table does not exist')
conn.close()