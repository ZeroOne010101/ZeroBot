import discord
from discord.ext import commands
from SECRETS import TOKEN
import logging

# setting up basic logging
logging.basicConfig(level=logging.INFO)


bot = commands.Bot(command_prefix='>')

bot.load_extension('extensions.googlecalendar.gcalendar_extension')

@bot.event
async def on_ready():
    print('Logged in as ' + str(bot.user))
    #channel = bot.get_channel(391732744977121281)
    #await channel.send('```' + '\n' + 'Bot online!' + '```')

    

@bot.command(name= 'ping')
async def _ping(message):
    await message.channel.send('```Pong!```')













# @bot.group()
# async def git(ctx):
#     if ctx.invoked_subcommand is None:
#         await ctx.send('Invalid git command passed...')

# @git.command()
# async def push(ctx, remote: str, branch: str):
#     await ctx.send('Pushing to {} {}'.format(remote, branch))










bot.run(TOKEN)



