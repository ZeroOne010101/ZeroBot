import discord
from discord.ext import tasks, commands

import aiosqlite

class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_guild_owner(self):
        async def predicate(ctx):
            if ctx.message.author == ctx.guild.owner:
                return True
            else: False
        return commands.check(predicate)
    
    @commands.command()
    @commands.check(is_guild_owner)
    async def add_calendar(self, ctx, *, calendar_id:str, *, notification_channel_id:str):
        if calendar_id != None and notification_channel_id != None:
            async with aiosqlite.connect('D:\\Dateien\\Programmieren\\Python\\ZeroBot\\ZeroBot_db.sqlite') as db:
                await db.execute(f'INSERT INTO gcal_ext (gcal_calendar_ext, gcal_notification_channel) VALUES ({calendar_id}, {notification_channel_id});')
                await db.commit()
        else:
            ctx.send('Either the calendar id or the notification channel id has not been passed.\nPlease make sure that your arguments match the format specified in the >>help command')
    
    # add error handler decorators

    # @commands.command()
    # @commands.check(is_guild_owner)
    # async def change_time_format(self, ctx, *, timeargs:str):
    #     pass
        

        