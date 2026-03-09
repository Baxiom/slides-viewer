import mysql.connector
from mysql.connector import errorcode
import config

def insert_into_db(query):
    cnx = None
    cursor = None
    try:
        cnx = mysql.connector.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database
        )
        if cnx.is_connected():
            print("Connection successful!")

        # Create a cursor object to execute SQL queries
        cursor = cnx.cursor()
        cursor.execute(query)
    except mysql.connector.Error as error :
        if error.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif error.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(error)
    finally:
        # Close the connection
        if cnx and cnx.is_connected():
            cnx.commit()
            cursor.close()
            cnx.close()

def make_insert_query(drive, filename, location, taken):
    return f'''INSERT INTO files ({drive}, {filename}, {location}, {taken})'''
