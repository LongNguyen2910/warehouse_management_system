from db_helper import get_db_connection
import pyodbc

def test_connection():
    print("checking connection...")
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            # Chạy thử một câu lệnh đơn giản nhất của SQL Server
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            
            print("ok")
            print(f"version: {row[0]}")
            
            # Kiểm tra xem có đọc được bảng Products không
            cursor.execute("SELECT COUNT(*) FROM Products")
            count = cursor.fetchone()[0]
            print(f"count: {count}")
            
            conn.close()
        except Exception as e:
            print(f"error {e}")
    else:
        print("error")

if __name__ == "__main__":
    test_connection()