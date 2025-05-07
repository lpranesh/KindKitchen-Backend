import psycopg2

def database():
    try:
        conn = psycopg2.connect(
            database="testdb",         # Your DB name
            user="postgres",           # Your PostgreSQL user
            password="12122005",       # Your DB password
            host="localhost",          # Your DB host (local server)
            port="5432"                # PostgreSQL default port
        )
        return conn
    except psycopg2.Error as e:
        print("Database connection failed:", e)
        raise e
