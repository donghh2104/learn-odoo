import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        user="odoo",
        password="odoo",
        dbname="postgres"
    )
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    rows = cur.fetchall()
    print("Databases available:")
    for row in rows:
        print(f"- {row[0]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
