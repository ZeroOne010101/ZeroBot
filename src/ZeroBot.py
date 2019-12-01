import discord
from discord.ext import tasks, commands
import logging
import aiosqlite #async bridge to the sqlite3 module
from os import environ
import json
import pathlib

# Set environment variables
# TODO: Will be replaced by dockerfile
with open('src/AuthToken.env') as dotenv:
    for line in dotenv:
        line = line.split('=')
        line[1] = line[1].replace('\"','')
        environ[line[0]]=line[1]

# setting base path
path = pathlib.Path('d:/Dateien/Programmieren/Python/ZeroBot')

# Setting up basic logging TODO: properly log and add logfile before deploy
logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d.%m.%Y %H:%M:%S')

# Gets prefixes from db
async def get_prefix(bot, ctx):
    prefixes = '!'
    if not ctx.guild: # Use default prefix in dm's
        return commands.when_mentioned_or(prefixes)(bot, ctx)

    async with aiosqlite.connect(path /'data'/'ZeroBotDB.db') as db:
        dbresults = await db.execute(f'SELECT prefix FROM guilds WHERE guildID == {str(ctx.guild.id)}')
        dbresults = await dbresults.fetchall() # looks like this: [('xy',)]
        if dbresults != []:
            prefixes = dbresults[0][0] # hence this
    return commands.when_mentioned_or(prefixes)(bot, ctx)

# Define stuff for the commands extension
bot = commands.Bot(command_prefix=get_prefix, owner_id=318774395189460994)

# TODO: Implement extensions
bot.load_extension('cogs.admincommands') # TODO: DEBUG, REMOVE ON DEPLOY
# with open('settings.json') as settings_file:
#     settings = json.load(settings_file)
#     for extension in settings['extensions']:
#             bot.load_extension(extension)

# Readycheck. dont do anything bot related before that
@bot.event
async def on_ready():
    print('The bot is now ready!')
    print(f'Logged in as {bot.user}')
    logging.info(f'Logged in as {bot.user}')

# Basic ping command
@bot.command()
async def ping(message):
    await message.channel.send(f'Pong! :ping_pong:\n```The bot has {bot.latency}s latency.```')

# TODO: find way to get guilds after downtime using bot.guilds,
# should only run once on start and delete removed and add joined guilds.

# Add guild to db if it gets invited
@bot.event
async def on_guild_join(guild):
    pass

# Remove guild from db if it gets kicked
@bot.event
async def on_guild_remove(guild):
    pass

##### Cog load/unload/reload commands #####
# These commands are not to be placed in cogs,
# as their purpose is to unload them.

@commands.is_owner()
@bot.command(hidden=True)
async def load(ctx, *, module):
    """Loads a module."""
    try:
        bot.load_extension(f'cogs.{module}')
    except commands.ExtensionError as e:
        await ctx.send(f'{e.__class__.__name__}: {e}')
    else:
        await ctx.send(':thumbsup:')

@commands.is_owner()
@bot.command(hidden=True)
async def unload(ctx, *, module):
    """Unloads a module."""
    try:
        bot.unload_extension(f'cogs.{module}')
    except commands.ExtensionError as e:
        await ctx.send(f'{e.__class__.__name__}: {e}')
    else:
        await ctx.send(':thumbsup:')

@commands.is_owner()
@bot.command(hidden=True)
async def reload(ctx, *, module):
    """Reloads a module."""
    try:
        bot.reload_extension(f'cogs.{module}')
    except commands.ExtensionError as e:
        await ctx.send(f'{e.__class__.__name__}: {e}')
    else:
        await ctx.send(':thumbsup:')

@commands.is_owner()
@bot.command(hidden=True)
async def loaded(ctx):
    """Reports all loded modules."""
    await ctx.channel.send(f'```{bot.extensions}```')

##### LEGACY BELOW #####
"""

# for messaging the bots owner(see on_ready)
bot_owner = None 


# ToDo: - set checks for the case someone decides to message the bot per pm.
#       - make nice help command that only features commands that users can use, use the description function
#       - add guilds that the bot is already in to the db
#       - add error decorators
#       - add state command

with open('settings.json') as settings_file:
    settings = json.load(settings_file)
    for extension in settings['extensions']:
            bot.load_extension(extension)

# basic ping to verify the base bot is working
@bot.command()
async def ping(message):
    await message.channel.send('```Pong!```')
    await message.channel.send(f'The bot has {bot.latency} s latency')

# add servers to db if it gets invited
@bot.event
async def on_guild_join(guild):
    async with aiosqlite.connect('D:\\Dateien\\Programmieren\\Python\\ZeroBot\\ZeroBot_db.sqlite') as db:
        _db_rowid_check = await db.execute('SELECT srv_id FROM servers ORDER BY srv_id DESC LIMIT 1;')
        _db_rowid_check = await _db_rowid_check.fetchall()
        if _db_rowid_check[0][0] >= 9000:
            await bot_owner.send('srv_id is over 9000! fix the db!')
        await db.execute(f'INSERT INTO servers (server) VALUES (\'{guild}\');')
        await db.commit()

# removes servers to db if it gets kicked
@bot.event
async def on_guild_remove(guild):
    async with aiosqlite.connect('D:\\Dateien\\Programmieren\\Python\\ZeroBot\\ZeroBot_db.sqlite') as db:
        await db.execute(f'DELETE FROM servers WHERE server = \'{guild}\';')
        await db.commit()
"""

bot.run(environ.get('ZEROBOT_AUTH_TOKEN'))