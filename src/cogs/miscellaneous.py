from discord.ext import commands

class MiscellaneousCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, words):
        await ctx.send(words)

def setup(bot):
    bot.add_cog(MiscellaneousCog(bot))