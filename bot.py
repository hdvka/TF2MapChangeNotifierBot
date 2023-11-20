# bot.py
import os
import a2s
import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = int(os.getenv("SERVER_PORT"))
SERVER_ADDRESS = (SERVER_IP, SERVER_PORT)
STEAM_NAME = os.getenv("STEAM_NAME")

intents = discord.Intents.default() 
intents.message_content = True  # Enable message content intent

bot = commands.Bot(intents=intents, command_prefix='!')

last_map = "fake_map"  # Global variable to store the last known map

async def check_map_periodically(address):
    global last_map
    while True:
        current_map = get_map(address)
        if current_map != last_map and not am_i_playing(address):
            channel = discord.utils.get(bot.get_all_channels(), name='general')  # Replace 'general' with your channel name
            if channel:
                await channel.send(f"The map has changed to: {current_map}")
            last_map = current_map
        await asyncio.sleep(30)  # Wait for 30 seconds before checking again

@bot.event
async def on_ready():
    bot.loop.create_task(check_map_periodically(SERVER_ADDRESS))

@bot.command(name='current_map', help='Current map of Uncletopia Chicago 1.')
async def current_map(ctx):
    await ctx.send(get_map(SERVER_ADDRESS))

def get_map(address):
    info = a2s.info(address)
    return info.map_name

def am_i_playing(address):
    players = a2s.players(address)
    return any(player.name == STEAM_NAME for player in players)

bot.run(TOKEN)