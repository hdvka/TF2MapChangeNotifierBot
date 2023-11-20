import sqlite3

map_file_path = 'data/maps.txt'
server_file_path = 'data/servers.txt'

with open(map_file_path, 'r') as file:
    map_data = file.read()

map_lines = map_data.strip().split('\n')

with open(server_file_path, 'r') as file:
    server_data = file.read()

server_lines = server_data.strip().split('\n')

conn = sqlite3.connect('tf2.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS maps (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS servers (
        id INTEGER PRIMARY KEY,
        ip TEXT NOT NULL,
        port INTEGER NOT NULL,
        name TEXT NOT NULL,
        map_type TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS map_server_usage (
        id INT PRIMARY KEY,
        map_id INT,
        server_id INT,
        play_count INT DEFAULT 0,
        last_played DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (map_id) REFERENCES maps(id),
        FOREIGN KEY (server_id) REFERENCES servers(id)
    )
''')

for map_name in map_lines:
    cursor.execute('INSERT INTO maps (name) VALUES (?)', (map_name,))

# Function to parse and insert data into the database
def parse_and_insert(data):
    for line in data:
        parts = line.split('"')
        ip_port = parts[0].strip().split(':')
        ip = ip_port[0].strip()
        port = int(ip_port[1].strip())
        name = parts[1].strip()
        map_type = parts[2].strip().strip('()')
        
        cursor.execute('INSERT INTO servers (ip, port, name, map_type) VALUES (?, ?, ?, ?)', (ip, port, name, map_type))

# Parse and insert the data
parse_and_insert(server_lines)


conn.commit()
conn.close()