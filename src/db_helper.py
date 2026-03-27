import pyodbc
import os
from flask import jsonify
from dotenv import load_dotenv

load_dotenv()

driver = os.getenv("DB_DRIVER")
server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
trusted = os.getenv("DB_TRUSTED_CONNECTION")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")


def get_db_connection():
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};"
    if trusted.lower() == 'yes':
        connection_string += "Trusted_Connection=yes;"
    else:
        connection_string += f"UID={user};PWD={password};TrustServerCertificate=yes;"
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error Database connection: {e}")
        return None

def row_to_dict(cursor, row):
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def query_db(query, args=(), one=False):
    conn = get_db_connection()
    if conn is None: return None
    
    cursor = conn.cursor()
    cursor.execute(query, args)
    
    columns = [column[0] for column in cursor.description]
    
    result = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return (result[0] if result else None) if one else result

def execute_db(query, args=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    conn.close()
    return True