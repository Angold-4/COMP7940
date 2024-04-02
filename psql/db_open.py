import os
import psycopg2

def create_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASS'],
            host=os.environ['DB_HOST'],
            port=os.environ['DB_PORT']
        )
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
    if conn is not None:
        fetch_data(conn)
