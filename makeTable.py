import sqlite3

try:
    connection = sqlite3.connect(f'time.db')
    cursor = connection.cursor()
    print("Opened Database successfully")
except Exception as e:
    print("Had errors opening database")
    raise e

connection.execute('''CREATE TABLE time
            (DATE       DATE    NOT NULL,
            CATEGORY            TEXT    NOT NULL,
            HOURS               INT     NOT NULL);''')

print("Table successully created")
