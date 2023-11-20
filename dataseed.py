import sqlite3

# Path to the file containing the map list
file_path = 'maps.txt'  # Adjust the path if the file is in a different directory

# Read data from the file
with open(file_path, 'r') as file:
    data = file.read()

# Splitting the data into lines
lines = data.strip().split('\n')

# Database connection
conn = sqlite3.connect('/mnt/data/tf2.db')
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS maps (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
''')

# Insert data into the database
for map_name in lines:
    cursor.execute('INSERT INTO maps (name) VALUES (?)', (map_name,))

# Commit changes and close connection
conn.commit()
conn.close()