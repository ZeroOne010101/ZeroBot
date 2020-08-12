from discord.ext import commands
from __main__ import dbPool
import logging
from asyncpg import PostgresError

class Control(commands.Cog):
    """Cog that contains settings for server admins"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """Add, remove or view prefixes.
        Lists all active prefixes if no argumants are given."""
        prefixString = ""
        try:
            async with dbPool.acquire() as conn:
                async with conn.transaction():
                    dbRecords = await conn.fetch("SELECT prefix FROM prefixes WHERE fk = (SELECT id FROM guilds WHERE guild_id = $1);", ctx.guild.id)
                    for dbRecord in dbRecords:
                        prefixString += f"{dbRecord['prefix']} "
            if prefixString != "":
                await ctx.send(f"```{prefixString[:-1]}```")
            else:
                await ctx.send(f"```No prefix set, default is ! or @ZeroBot```")
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error

    @prefix.command()
    async def set(self, ctx, prefix):
        """Adds a prefix.
        If this is the first prefix added for a server, it overrides the default prefix."""
        try:
            async with dbPool.acquire() as conn:
                async with conn.transaction():
                    guildId = await conn.fetchval("SELECT id FROM guilds WHERE guild_id = $1;", ctx.guild.id)
                    await conn.execute("INSERT INTO prefixes VALUES ($1, $2);", guildId, prefix)
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error

    @prefix.command()
    async def remove(self, ctx, prefix):
        """Removes a prefix.
        If all prefixes are removed, the prefix reverts to the default."""
        try:
            async with dbPool.acquire() as conn:
                async with conn.transaction():
                    guildId = await conn.fetchval("SELECT id FROM guilds WHERE guild_id = $1;", ctx.guild.id)
                    await conn.execute("DELETE FROM prefixes WHERE fk=$1 AND prefix=$2;", guildId, prefix)
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error

def setup(bot):
    bot.add_cog(Control(bot))