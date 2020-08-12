from discord.ext import commands
import logging
import asyncpg
from os import chdir
import json
import pathlib

# Setting base path
path = pathlib.Path('d:/Dateien/Programmieren/Python/ZeroBot')
chdir(path)

# Setting up basic logging TODO: properly log and add logfile before deploy
logging.basicConfig(format="[%(asctime)s] %(levelname)s:%(message)s", level=logging.INFO, datefmt="%d.%m.%Y %H:%M:%S", filename="data/logfile.log")

# Load Settings
botSettings = None
with open(path / 'data' / 'settings.json', mode='r') as settingsFile:
    botSettings = json.load(settingsFile)

# Setup database connection pool
dbSettings = botSettings['postgres']
dbPool = None
async def initialize_pool():
    global dbPool
    dbPool = await asyncpg.create_pool(host=dbSettings['pgHost'],
                                    user=dbSettings['pgUser'], 
                                    password=dbSettings['pgPassword'],
                                    database=dbSettings['pgDatabase'])

# Gets prefixes from db
async def get_prefix(bot, ctx):
    async with dbPool.acquire() as conn:
        async with conn.transaction():
            dbRecords = await conn.fetch('SELECT prefix FROM prefixes WHERE fk = (SELECT id FROM guilds WHERE guild_id = $1);', ctx.guild.id)
            if dbRecords:
                if len(dbRecords) > 1:
                    prefixes = [dbRecord['prefix'] for dbRecord in dbRecords]
                else:
                    prefixes = [dbRecords[0]['prefix']]
            else:
                prefixes = ['!']
    return commands.when_mentioned_or(*prefixes)(bot, ctx)

# Define bot
bot = commands.Bot(command_prefix=get_prefix, owner_id=318774395189460994)

# Checks if the bot is ready. Nothing executes boefore the check has passed.
@bot.event
async def on_ready():
    logging.info('The bot is now ready!')
    logging.info(f'Logged in as {bot.user}')
    # Initialize database pool
    await initialize_pool()
    
    # Load cogs from settings file
    for cogStr in botSettings['cogs']:
        bot.load_extension(cogStr)
    # Add guilds that the bot is part of to db if not already in there
    async with dbPool.acquire() as conn:
        dbGuildIdList = []
        dbGuildIdRecords = await conn.fetch('SELECT guild_id FROM guilds;')
        for record in dbGuildIdRecords:
            dbGuildIdList.append(record['guild_id'])
        for guild in bot.guilds:
            if guild.id not in dbGuildIdList:
                async with conn.transaction():
                    await conn.execute('INSERT INTO guilds(guild_id) VALUES($1);', guild.id)

@bot.command()
async def ping(ctx):
    """Reports the bots latency."""
    await ctx.channel.send(f'Pong! :ping_pong:\n```The bot has {bot.latency}s latency.```')

# Add guild to db if it gets invited
@bot.event
async def on_guild_join(guild):
    async with dbPool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('INSERT INTO guilds(guild_id) VALUES($1);', guild.id)

# Remove guild from db if it gets kicked
@bot.event
async def on_guild_remove(guild):
    async with dbPool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('DELETE FROM guilds WHERE guild_id = $1;', guild.id)

##### Cog load/unload/reload commands #####
# These commands are not to be placed in cogs,
# as their purpose is to load/unload them.

@commands.is_owner()
@bot.command(hidden=True)
async def load(ctx, *, module):
    """Loads a module."""
    try:
        bot.load_extension(f'cogs.{module}')
    except commands.ExtensionError as e:
        logging.error(f'{e.__class__.__name__}: {e}')
        await ctx.send(f'{e.__class__.__name__}: {e}')
        raise e
    else:
        logging.info(f'module cogs.{module} was loaded successfully')
        await ctx.send(':thumbsup:')

@commands.is_owner()
@bot.command(hidden=True)
async def unload(ctx, *, module):
    """Unloads a module."""
    try:
        bot.unload_extension(f'cogs.{module}')
    except commands.ExtensionError as e:
        logging.error(f'{e.__class__.__name__}: {e}')
        await ctx.send(f'{e.__class__.__name__}: {e}')
        raise e
    else:
        logging.info(f'module cogs.{module} was unloaded successfully')
        await ctx.send(':thumbsup:')

@commands.is_owner()
@bot.command(hidden=True)
async def reload(ctx, *, module):
    """Reloads a module."""
    try:
        bot.reload_extension(f'cogs.{module}')
    except commands.ExtensionError as e:
        logging.error(f'{e.__class__.__name__}: {e}')
        await ctx.send(f'{e.__class__.__name__}: {e}')
        raise e
    else:
        logging.info(f'module cogs.{module} was reloaded successfully')
        await ctx.send(':thumbsup:')

@commands.is_owner()
@bot.command(hidden=True)
async def loaded(ctx):
    """Reports all loded modules."""
    await ctx.channel.send(f'```{bot.extensions}```')

# TODO add restrictions in control
bot.run(botSettings['token'])