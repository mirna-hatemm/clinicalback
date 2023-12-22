import  bcrypt
from database import get_cursor, commit
from flask import jsonify

# ... your login function ...



def signup(username, password, email, user_type):
    cursor = get_cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute("SELECT * FROM doctorsdata WHERE Username = %s", (username,))
    doctor_user = cursor.fetchone()

    cursor.execute("SELECT * FROM patientsdata WHERE Username = %s", (username,))
    patient_user = cursor.fetchone()

    if doctor_user or patient_user:
        return "Username already exists!"

    if user_type == "doctor":
        table_name = "doctorsdata"
    elif user_type == "patient":
        table_name = "patientsdata"
    else:
        return "Invalid user type!"

    cursor.execute(
        f"INSERT INTO {table_name} (Username, Password, Email) VALUES (%s, %s, %s)",
        (username, hashed, email)
    )
    commit()
    return "User registered successfully!"



def login(username, password, user_type):
    cursor = get_cursor()

    # Check for a valid user type
    if user_type not in ["doctor", "patient"]:
        return {'message': "Invalid user type!"}, 400  # Bad Request for invalid user type

    # Determine the table based on the user type
    table_name = "doctorsdata" if user_type == "doctor" else "patientsdata"

    print(f"Checking in {table_name} table for user {username}.")
    cursor.execute(f"SELECT Password FROM {table_name} WHERE Username = %s", (username,))
    user = cursor.fetchone()

    # User not found
    if not user:
        return {'message': 'Login failed'}, 401  # Unauthorized

    # Check password
    if bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
        return {'message': 'Login Successful! Welcome, ' + username}, 200
    else:
        return {'message': 'Invalid password'}, 401  # Unauthorized









