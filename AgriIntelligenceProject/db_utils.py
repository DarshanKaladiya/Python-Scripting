import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection(db_name='agri_intelligence'):
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=db_name
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def init_db():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "")
    )
    cursor = conn.cursor()
    
    with open('schema.sql', 'r') as f:
        # Use simple split for now but ensure we handle comments and empty blocks
        sql_file = f.read()
        sql_commands = sql_file.split(';')
        
    for command in sql_commands:
        clean_command = command.strip()
        if clean_command:
            try:
                cursor.execute(clean_command)
            except mysql.connector.Error as err:
                print(f"Failed to execute command: {clean_command[:50]}...")
                print(f"Error: {err}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Database and Tables Initialized!")

if __name__ == "__main__":
    init_db()
