import discord
from discord.ext import commands
import os

def setup(bot):
    bot.add_cog(admincommands(bot))

class admincommands(commands.Cog):
    def __init__(self, bot):
        self.bot_owner = bot_owner
    
    @commands.command()
    @commands.is_owner()
    async def get_log(self):
        await self.bot_owner.send('Here are you\'r logs, sir.', file=discord.File('log.txt')) # implement logfile before deploy and test function
