from discord.ext import commands
import logging
import pathlib
import aiosqlite

# Setting up path
path = pathlib.Path('d:/Dateien/Programmieren/Python/ZeroBot')

#TODO: Set up proper logging

class AdmincommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    ##### Commands #####
    @commands.is_owner()
    @commands.group(hidden=True,invoke_without_command=True)
    async def message(self, ctx, userID, *, message):
        user = self.bot.get_user(int(userID))
        await user.send(message)

    @message.command()
    async def admins(self, ctx, *, message):
        for guild in self.bot.guilds:
            await guild.owner.send(message)
    
    @message.command()
    @commands.guild_only()
    async def role(self, ctx, roleID, *, message):
        print(int(roleID))
        role = ctx.guild.get_role(int(roleID))
        for member in role.members:
            await member.send(message)
    
    ##### Error handling #####
    @message.error
    @role.error
    async def message_error(self, ctx, error):
        if isinstance(error, ValueError):
            await ctx.channel.send(f'Invalid userID or roleID')

def setup(bot):
    bot.add_cog(AdmincommandsCog(bot))