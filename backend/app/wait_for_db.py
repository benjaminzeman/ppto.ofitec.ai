import os, time
import sys
import psycopg2

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "ofitec")
DB_USER = os.getenv("POSTGRES_USER", "ofitec")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "ofitec")

max_attempts = 30
for attempt in range(1, max_attempts + 1):
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        conn.close()
        print(f"Database is ready (attempt {attempt}).")
        break
    except Exception as e:
        print(f"Waiting for database... attempt {attempt}/{max_attempts} - {e}")
        time.sleep(2)
else:
    print("Database not ready after max attempts", file=sys.stderr)
    sys.exit(1)

# Continue to app startup
