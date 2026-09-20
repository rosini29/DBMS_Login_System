import datetime
import pyodbc
import bcrypt
from database import get_connection

def hash_password(plain_password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a generated salt.
    Returns the resulting hash decoded as a UTF-8 string.
    """
    # Encode password string to bytes
    password_bytes = plain_password.encode("utf-8")
    # Generate salt (default work factor = 12)
    salt = bcrypt.gensalt(rounds=12)
    # Hash the password
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # Return string representation for database storage
    return hashed_bytes.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies whether a plaintext password matches the stored bcrypt hash.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def username_exists(cursor, username: str) -> bool:
    """
    Checks if a given username already exists in the Users table.
    Uses parameterized query to prevent SQL Injection.
    """
    query = "SELECT COUNT(*) FROM Users WHERE Username = ?"
    cursor.execute(query, (username,))
    count = cursor.fetchone()[0]
    return count > 0

def register_user(full_name: str, username: str, password: str, email: str) -> tuple:
    """
    Registers a new user record in Microsoft Access.
    Returns (success: bool, message: str).
    """
    # Validation checks
    full_name = full_name.strip()
    username = username.strip()
    email = email.strip()
    
    if not full_name or not username or not password or not email:
        return False, "Error: All fields are required and cannot be blank."
    
    if len(username) < 3:
        return False, "Error: Username must be at least 3 characters long."
    
    if len(password) < 6:
        return False, "Error: Password must be at least 6 characters long."
    
    if "@" not in email or "." not in email:
        return False, "Error: Please enter a valid email address."
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check for duplicate username
        if username_exists(cursor, username):
            conn.close()
            return False, f"Error: Username '{username}' is already taken. Please choose another."
        
        # Hash password securely
        hashed_pw = hash_password(password)
        registered_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Parameterized INSERT query
        insert_query = (
            "INSERT INTO Users (FullName, Username, PasswordHash, Email, DateRegistered) "
            "VALUES (?, ?, ?, ?, ?)"
        )
        cursor.execute(insert_query, (full_name, username, hashed_pw, email, registered_date))
        conn.commit()
        conn.close()
        return True, "Registration successful! You may now log in."
    except pyodbc.Error as ex:
        return False, f"Database Error during registration: {ex}"
    except Exception as ex:
        return False, f"Unexpected Error: {ex}"

def login_user(username: str, password: str) -> tuple:
    """
    Authenticates a user against the Users table.
    Returns (success: bool, message: str, user_data: dict or None).
    """
    username = username.strip()
    if not username or not password:
        return False, "Username and password cannot be empty.", None
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Parameterized SELECT query
        select_query = (
            "SELECT UserID, FullName, Username, PasswordHash, Email, DateRegistered "
            "FROM Users WHERE Username = ?"
        )
        cursor.execute(select_query, (username,))
        row = cursor.fetchone()
        conn.close()
        
        # If user record was not found
        if row is None:
            return False, "Invalid username or password.", None
        
        user_id, full_name, db_username, stored_hash, email, date_registered = row
        
        # Verify bcrypt hash
        if verify_password(password, stored_hash):
            user_payload = {
                "user_id": user_id,
                "full_name": full_name,
                "username": db_username,
                "email": email,
                "date_registered": str(date_registered)
            }
            return True, "Login successful!", user_payload
        else:
            return False, "Invalid username or password.", None
            
    except pyodbc.Error as ex:
        return False, f"Database Error during login: {ex}", None
    except Exception as ex:
        return False, f"Unexpected Error: {ex}", None