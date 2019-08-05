import discord
from discord.ext import commands
import os

os.chdir('D:\\Dateien\\Programmieren\\Python\\ZeroBot')

class admincommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.is_owner()
    async def get_log(self):
        await self.bot.owner.send('Here are you\'r logs, sir.', file=discord.File('discordlog.log')) # implement logfile before deploy and test function

def setup(bot):
    bot.add_cog(admincommands(bot))