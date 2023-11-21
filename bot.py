# bot.py
import os
import a2s
import asyncio
import discord
import sqlite3
from dotenv import load_dotenv
from discord.ext import commands
from models import Map, Server, ServerMapChange

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
STEAM_NAME = os.getenv("STEAM_NAME")
FAVE_SERVER_ID = os.getenv("FAVE_SERVER_ID")

intents = discord.Intents.default() 
intents.message_content = True  # Enable message content intent

bot = commands.Bot(intents=intents, command_prefix='!')

last_map = "fake_map"  # Global variable to store the last known map

def initialize_data():
    conn = sqlite3.connect('tf2.db')
    cursor = conn.cursor()

    servers_query = '''
        SELECT id, ip, port, name, map_type FROM servers
    '''

    cursor.execute(servers_query)

    raw_servers = cursor.fetchall()
    servers = [Server(
        id=server[0], ip=server[1], port=server[2], name=server[3], map_type=server[4]
        ) for server in raw_servers]

    maps_query = '''
        SELECT id, name FROM maps
    '''

    cursor.execute(maps_query)

    raw_maps = cursor.fetchall()
    maps = [Map(
        id=tf2_map[0], name=tf2_map[1]
        ) for tf2_map in raw_maps]

    conn.close()

    return (servers, maps)

(servers, maps) = initialize_data()

# If the fave server ID isn't present, just grab the first one (which is conveniently my fave anyway)
fave_server_entry = next(filter(lambda x: x.id == FAVE_SERVER_ID, servers), servers[0])
FAVE_SERVER_ADDRESS = (fave_server_entry.ip, fave_server_entry.port)

def get_most_recent_map_name(server):
    conn = sqlite3.connect('tf2.db')
    cursor = conn.cursor()

    select_sql = '''
    SELECT m.name FROM maps m
    LEFT JOIN server_map_changes smc ON m.id = smc.map_id
    WHERE smc.server_id = ?
    ORDER BY smc.created DESC
    LIMIT 1
    '''

    cursor.execute(select_sql, (server.id,))

    result = cursor.fetchone()

    conn.close()

    return result[0] if result else None

def record_server_map_change(server, map_name):
    conn = sqlite3.connect('tf2.db')
    cursor = conn.cursor()

    select_sql = '''
    SELECT id FROM maps WHERE name = ?
    '''

    cursor.execute(select_sql, (map_name,))

    map_id_tuple = cursor.fetchone()
    if map_id_tuple:
        insert_sql = '''
        INSERT INTO server_map_changes (map_id, server_id, player_count) 
        VALUES (?, ?, ?)
        '''

        player_count = 24 # TODO: Make this dynamic

        cursor.execute(insert_sql, (map_id_tuple[0], server.id, player_count))

        conn.close()
    else:
        insert_sql = '''
        INSERT INTO maps (name) 
        VALUES (?)
        '''

        cursor.execute(insert_sql, (map_name,))

        conn.close()

        record_server_map_change(server, map_name)

async def check_map_periodically(server):
    while True:
        current_map_name = await get_map(server.address)
        if current_map_name is not None:
            most_recent_map_name = get_most_recent_map_name(server)
            if most_recent_map_name != current_map_name:
                record_server_map_change(server, current_map_name)
                playing = await am_i_playing_on_server(server.address)
                if playing is not None and not playing:
                    channel = discord.utils.get(bot.get_all_channels(), name='general')
                    if channel:
                        await channel.send(f"The map has changed to: {current_map_name}")
        await asyncio.sleep(60)  # Wait for 60 seconds before checking again

@bot.event
async def on_ready():
    for server in servers:
        bot.loop.create_task(check_map_periodically(server))
        await asyncio.sleep(4)  # stagger the tasks

@bot.command(name='current_map', help='Current map of Uncletopia Chicago 1.')
async def current_map_handler(ctx):
    await ctx.send(await get_map(FAVE_SERVER_ADDRESS))

@bot.command(name='am_i_playing', help='Am I on the currently monitored server?.')
async def am_i_playing_handler(ctx):
    await ctx.send(await am_i_playing())

async def get_map(address):
    try:
        info = await a2s.ainfo(address)
        return info.map_name
    except:
        return None

async def am_i_playing():
    playing = False
    for server in servers:
        server_address = (server.ip, server.port)
        playing_on_server = await am_i_playing_on_server(server_address)
        if playing_on_server:
            playing = True
            break
    return playing

async def am_i_playing_on_server(address):
    try:
        players = await a2s.aplayers(address=address)
        return any(player.name == STEAM_NAME for player in players)
    except:
        return None

bot.run(TOKEN)