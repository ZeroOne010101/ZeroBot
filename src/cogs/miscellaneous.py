from discord.ext import commands

class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, words):
        """Makes the bot repeat what you say."""
        await ctx.send(words)

def setup(bot):
    bot.add_cog(Miscellaneous(bot))