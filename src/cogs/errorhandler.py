from discord import errors
from discord.ext import commands
import logging
import pathlib

# Setting up path
path = pathlib.Path('d:/Dateien/Programmieren/Python/ZeroBot')

#TODO: Set up proper logging

class ErrorhandlerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.channel.send(f'Missing argument: {error.param}')

        else:
            print(error)
            await ctx.channel.send(f'```IMPORTANT: please report this error to the bots owner.```Unknown Error: ```{error}```')

def setup(bot):
    bot.add_cog(ErrorhandlerCog(bot))