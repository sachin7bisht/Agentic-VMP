
from src.core.db_manager import db_manager
import logging

# basic setup
logging.basicConfig(level=logging.INFO)

def check_vendor():
    email = "jchavez@gmail.com"
    query = "SELECT * FROM vendors WHERE email = ?"
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (email,))
        row = cursor.fetchone()
        if row:
            print("Row found:", dict(row))
        else:
            print("Row not found for", email)

if __name__ == "__main__":
    check_vendor()
