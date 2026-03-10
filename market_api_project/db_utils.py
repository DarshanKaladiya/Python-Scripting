import mysql.connector

def get_connection(db_name="internship_analysis"):
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=db_name
        )
    except mysql.connector.Error as err:
        print(f"Connection Error: {err}")
        return None