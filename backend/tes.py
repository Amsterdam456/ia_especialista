import sqlite3
con = sqlite3.connect("data/athena.db")
cur = con.cursor()
cur.execute("DELETE FROM alembic_version")
con.commit()
con.close()
print("alembic_version limpo")