import os
import pyodbc

# Define relative database path
DB_FILENAME = "UserSystem.accdb"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, DB_FILENAME)

def get_connection():
    """
    Establishes and returns a connection to the Microsoft Access database.
    Uses the official Microsoft Access Driver (*.mdb, *.accdb).
    """
    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError(
            f"Database file not found: {DATABASE_PATH}\n"
            f"Please ensure {DB_FILENAME} exists in the project root directory."
        )

    connection_string = (
        r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={DATABASE_PATH};"
    )
    return pyodbc.connect(connection_string)

def test_connection():
    """
    Tests the database connection and verifies table accessibility.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"Database connected successfully! Total users in database: {count}")
        return True
    except pyodbc.Error as ex:
        print(f"ODBC Connection Error: {ex}")
        return False
    except Exception as ex:
        print(f"General Error: {ex}")
        return False

if __name__ == "__main__":
    print("Testing connection to Microsoft Access...")
    test_connection()
