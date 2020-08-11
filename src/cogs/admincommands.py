from discord.ext import commands
import logging

class AdmincommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    ##### Commands #####
    @commands.is_owner()
    @commands.command(hidden=True)
    async def close(self, ctx):
        """Closes connection to discord"""
        await ctx.send("```Are you sure you want to close the bot? (y/n)```")
        confirmation = await self.bot.wait_for("message")
        if confirmation.content == "y":
            logging.info("The \"close\" command has been invoked.")
            await self.bot.close()
        else:
            logging.info("The \"close\" command has been aborted.")
            await ctx.send("```The \"close\" command has been aborted.```")

    @commands.is_owner()
    @commands.group(name='message', hidden=True, invoke_without_command=True)
    async def message(self, ctx, userID, *, message):
        user = self.bot.get_user(int(userID))
        await user.send(message)

    @commands.is_owner()
    @message.command(name='admins')
    async def admins(self, ctx, *, message):
        for guild in self.bot.guilds:
            await guild.owner.send(message)

    @commands.is_owner()
    @commands.guild_only()
    @message.command(name='role')
    async def role(self, ctx, roleID, *, message):
        role = ctx.guild.get_role(int(roleID))
        for member in role.members:
            await member.send(message)
    
    ##### Error handling #####
    @message.error
    @role.error
    async def id_errhandling(self, ctx, error):
        if isinstance(error, ValueError):
            await ctx.channel.send(f"```Invalid userID or roleID```")
        else:
            await ctx.channel.send(f"```{error.__class__.__name__}: {error}```")


def setup(bot):
    bot.add_cog(AdmincommandsCog(bot))