# bot.py
import os
import a2s
import asyncio
import discord
import logging
from dotenv import load_dotenv
from discord.ext import commands

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

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
        current_map = await get_map(address)
        if current_map != last_map:
            playing = await am_i_playing(address)
            if not playing:
                channel = discord.utils.get(bot.get_all_channels(), name='general')
                if channel:
                    await channel.send(f"The map has changed to: {current_map}")
                last_map = current_map
        await asyncio.sleep(30)  # Wait for 30 seconds before checking again

@bot.event
async def on_ready():
    bot.loop.create_task(check_map_periodically(SERVER_ADDRESS))

@bot.command(name='current_map', help='Current map of Uncletopia Chicago 1.')
async def current_map_handler(ctx):
    await ctx.send(await get_map(SERVER_ADDRESS))

@bot.command(name='am_i_playing', help='Am I on the currently monitored server?.')
async def am_i_playing_handler(ctx):
    await ctx.send(await am_i_playing(SERVER_ADDRESS))

""" @bot.command(name='what_am_i_playing', help='What am I playing according to Discord?')
async def activity(ctx, user: discord.Member):
    try:
        for activity in user.activities:
            if activity.type == discord.ActivityType.playing:
                await ctx.send(f"{user.name} is playing {activity.name}")
                return
        await ctx.send(f"{user.name} is not playing anything.")
    except discord.NotFound:
        await ctx.send("User not found.") """

async def get_map(address):
    info = await a2s.ainfo(address)
    return info.map_name

async def am_i_playing(address):
    try:
        players = await a2s.aplayers(address=address)
        return any(player.name == STEAM_NAME for player in players)
    except:
        return False

bot.run(TOKEN)