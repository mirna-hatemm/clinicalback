import mysql.connector
import os

# Read database configuration from environment variables with default values
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', 'root')
db_name = os.getenv('DB_NAME', 'user')
print(f"Database Host: {db_host}")
print(f"Database User: {db_user}")
print("Database Password: [HIDDEN]")
print(f"Database Name: {db_name}")
# Connect to the database
db = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

def get_cursor():
    return db.cursor()

def commit():
    try:
        db.commit()
        print("Changes committed successfully.")
    except Exception as e:
        db.rollback()
        print("Error occurred during commit. Changes rolled back.")
        print("Error message:", str(e))
