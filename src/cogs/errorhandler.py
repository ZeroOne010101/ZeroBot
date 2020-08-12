from discord import errors
from discord.ext import commands
import logging
import traceback

class Errorhandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Prevents any commands with local handlers from being handled here.
        if hasattr(ctx.command, 'on_error'):
            return

        # Prevents any cogs with an overwritten cog_command_error from being handled here.
        if ctx.cog:
            if ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
                return

        # Do nothing if the error is ignored
        ignored = (commands.CommandNotFound, )
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f"```{ctx.command} is currently disabled```")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"```Missing argument: {error.param}```")

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"```{ctx.command} can not be used in private messages```")

        else:
            logging.info(f"Ignoring exception {error.__class__.__name__} in command {ctx.command} with message: {error}")
            with open("data/logfile.log", "a") as logfile:
                traceback.print_tb(error.__traceback__, file=logfile)
            raise error

def setup(bot):
    bot.add_cog(Errorhandler(bot))