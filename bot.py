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

def get_servers():
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

    conn.close()

    return servers

def get_top_ten():
    conn = sqlite3.connect('tf2.db')
    cursor = conn.cursor()

    top_ten_sql = """
        SELECT m.name, SUM(smc.player_count) AS total_players
        FROM server_map_changes smc
        LEFT JOIN maps m on m.id = smc.map_id
        GROUP BY map_id
        ORDER BY total_players DESC
        LIMIT 10
    """
    cursor.execute(top_ten_sql)

    raw_maps = cursor.fetchall()

    conn.close()

    return "\n".join([map[0] for map in raw_maps])

def get_most_recent_map_name(server, conn):
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

    return result[0] if result else None

def record_server_map_change(server, map_name, player_count, conn):
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

        conn.commit()

        cursor.execute(insert_sql, (map_id_tuple[0], server.id, player_count))
    else:
        insert_sql = '''
        INSERT INTO maps (name) 
        VALUES (?)
        '''

        cursor.execute(insert_sql, (map_name,))

        conn.commit()

        record_server_map_change(server, map_name, player_count, conn)

async def check_map_periodically(server):
    while True:
        current_map = await get_map(server.address)
        if current_map is not None:
            conn = sqlite3.connect('tf2.db')
            most_recent_map_name = get_most_recent_map_name(server, conn)
            if most_recent_map_name != current_map.map_name:
                record_server_map_change(server, current_map.map_name, current_map.player_count, conn)
                playing = await am_i_playing_on_server(server.address)
                if playing is not None and not playing and current_map.player_count > 10: # Adjust to taste
                    channel = discord.utils.get(bot.get_all_channels(), name='general')
                    if channel:
                        await channel.send(f"The map on **{server.name}** has changed to **{current_map.map_name}**")
            conn.commit()
            conn.close()
        await asyncio.sleep(60)  # Wait for 60 seconds before checking again

@bot.event
async def on_ready():
    for server in get_servers():
        bot.loop.create_task(check_map_periodically(server))
        await asyncio.sleep(4)  # stagger the tasks

@bot.command(name='current_map', help='Current map of favorited server.')
async def current_map_handler(ctx):
    servers = get_servers()
    # If the fave server ID isn't present, just grab the first one (which is conveniently my fave anyway)
    fave_server_entry = next(filter(lambda x: x.id == FAVE_SERVER_ID, servers), servers[0])
    await ctx.send((await get_map(fave_server_entry.address)).map_name)

@bot.command(name='am_i_playing', help='Am I playing on any server?')
async def am_i_playing_handler(ctx):
    await ctx.send(await am_i_playing())

@bot.command(name='top_ten', help='Top 10 most popular maps')
async def top_ten_handler(ctx):
    await ctx.send(get_top_ten())

async def get_map(address):
    try:
        info = await a2s.ainfo(address)
        return info
    except:
        return None

async def am_i_playing():
    playing = False
    for server in get_servers():
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