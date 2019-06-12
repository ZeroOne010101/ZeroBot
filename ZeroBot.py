import discord
from discord.ext import commands
from SECRETS import TOKEN
import logging
import aiosqlite #async bridge to the sqlite3 module
import os

# to insure that the working directory is correct (thanks windows for making this necessary. linux mvp)
os.chdir('D:\\Dateien\\Programmieren\\Python\\ZeroBot')

# setting up basic logging, to be changed to a logfile on deploy
logging.basicConfig(level=logging.INFO)


# Define stuff for the commands extension
bot = commands.Bot(command_prefix='>', owner_id=318774395189460994)

# for messaging the bots owner(see on_ready)
bot_owner = None 


# ToDo: - set checks for errors, and in case someone decides to message the bot per pm.
#       - set mngment group and commands, set restrains on them.
#       - make nice help command that only features commands that users can use, use the description function
#       - pack everything in cogs for clarity, consider using __main__.py restrictions for good practice.
#       - add guilds that the bot is already in to the db

# loading extensions
bot.load_extension('extensions.googlecalendar_extension')

# Readycheck. dont do anything bot related before that
@bot.event
async def on_ready():
    print('The bot is now ready!')
    print(f'Logged in as {str(bot.user)}')
    print(bot.user)
    bot_owner = bot.get_user(318774395189460994)
    await bot_owner.send('```' + '\n' + 'Bot online!' + '```')


# basic ping to verify the base bot is working
@bot.command()
async def ping(message):
    await message.channel.send('```Pong!```')

# add servers to db if it gets invited
@bot.event
async def on_guild_join(guild):
    async with aiosqlite.connect('D:\\Dateien\\Programmieren\\Python\\ZeroBot\\ZeroBot_db.sqlite') as db:
        _db_rowid_check = await db.execute('SELECT srv_id FROM servers ORDER BY srv_id DESC LIMIT 1;')
        _db_rowid_check = await _db_rowid_check.fetchall()
        if _db_rowid_check[0][0] <= 9000:
            await bot_owner.send('srv_id is over 9000! fix the db!')
        await db.execute(f'INSERT INTO servers (server) VALUES (\'{guild}\');')
        await db.commit()

# removes servers to db if it gets kicked
@bot.event
async def on_guild_remove(guild):
    async with aiosqlite.connect('D:\\Dateien\\Programmieren\\Python\\ZeroBot\\ZeroBot_db.sqlite') as db:
        await db.execute(f'DELETE FROM servers WHERE server = \'{guild}\';')
        await db.commit()

# admin & management commands from here. to be moved to extension file in the future, hence the minimal comments. dont forget to restrict access appropriately!
@bot.group
async def botadmincommand(ctx, name= 'botadmcmd'):
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid mngment command passed !')

# @bot.group
# async def management(ctx, name= 'mngment'):
#     if ctx.invoked_subcommand is None:
#         await ctx.send('Invalid mngment command passed !')

# @management.subcommand()
# async def set_gcalendar_notification_channel(ctx):
#     pass




bot.run(TOKEN)



