import psycopg2
from config import DATABASE_CONFIG

def create_connection():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except Exception as error:
        print(f"Error connecting to the database: {error}")
        return None

def fetch_data(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM your_table_name LIMIT 5;")
        records = cursor.fetchall()
        for row in records:
            print(row)
        cursor.close()
    except Exception as error:
        print(f"Error fetching data: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    conn = create_connection()
    if conn is not null:
        fetch_data(conn)
