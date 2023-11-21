# models.py

class Map:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Server:
    def __init__(self, id, ip, port, name, map_type):
        self.id = id
        self.ip = ip
        self.port = port
        self.name = name
        self.map_type = map_type
        self.address = (self.ip, self.port)

class ServerMapChange:
    def __init__(self, id, map_id, server_id, player_count, created):
        self.id = id
        self.map_id = map_id
        self.server_id = server_id
        self.player_count = player_count
        self.created = created
