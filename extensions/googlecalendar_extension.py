import discord
from discord.ext import tasks, commands

import googleapiclient.discovery
from google.oauth2 import service_account

import datetime
import os
import aiosqlite
import asyncio
import logging
import re


# ToDo: - make this compatible with the db and multiple guilds(attach guild id to output list?)
#       - find out how to give guilds the ability to set custom parameters(aka find out how to get the reminder time from google)
#       - bind functionality to tags. eg:[inage]
#       - parse image: url in the description, complete with error handling
#       - Find out if adding the service account to private calendars works. Else, issue instructions accordingly

os.chdir('D:\\Dateien\\Programmieren\\Python\\ZeroBot')

class GooglecalendarExtension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.gcal_notifier())
    
    async def gcal_notifier(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # get stuff from db
            async with aiosqlite.connect('D:\\Dateien\\Programmieren\\Python\\ZeroBot\\ZeroBot_db.sqlite') as db:
                calendar_dbdata =  await db.execute('SELECT gcal_calendar_id, gcal_notification_channel, format_reversed FROM gcal_ext;')
                calendar_dbdata = await calendar_dbdata.fetchall()
            for dbdata in calendar_dbdata:
                try:
                    eventdata = self.google_apiresponse_sorter(self.google_api_get_events(168, dbdata[0])) # ToDo: add try: except to it so id doesnt break on every invalid calendar address, and notify the guild owner (maybe: run this in executor so the bot doesnt slow down)
                except:
                    cid = dbdata[1]
                    self.notify_guild_owner('The Notification-Channel you provided seems to be incorrect.', channelid=cid)

                await self.send_calendarevent(dbdata[1], dbdata[2], eventdata)
            logging.info('GooglecalendarExtension.gcal_notifier just ran')
            await asyncio.sleep(2*60*60)


    async def send_calendarevent(self, channelid, format_reversed, eventdata):
        nchannel = self.bot.get_channel(channelid)

        # get all bot-messages in channel
        messages_to_delete = []
        async for message in nchannel.history(limit=100):
            if message.author == self.bot.user:
                messages_to_delete.append(message)
            
            # delete all messages in list
        try:
            await nchannel.delete_messages(messages_to_delete)
        except:
            logging.info('GooglecalendarExtension.send_calendarevent: Couldnt delete Messages')
            
        # loop thruogh the 0'th list with evtdtelementlen being the number of the current list-element
        for evtdtlistlen in range(len(eventdata[0])):
            embed = None
            # Title
            if eventdata[2][evtdtlistlen] != None:
                embed = discord.Embed(title=eventdata[2][evtdtlistlen])
            else:
                embed = discord.Embed(title='No Title Found')
                
            # Starttime
            if eventdata[0][evtdtlistlen] != None:
                # plug starttime into parser
                eventdata_start = self.date_parser(eventdata[0][evtdtlistlen], format_reversed)
                # add parsed string to embed
                embed.add_field(name='Start:', value=f'{eventdata_start}\n', inline=True)
            else:
                embed.add_field(name='Start:', value='No starttime found\n', inline=True)

            # Endtime
            if eventdata[1][evtdtlistlen] != None:
                eventdata_end = self.date_parser(eventdata[0][evtdtlistlen], format_reversed)
                embed.add_field(name='End:', value=f'{eventdata_end}\n', inline=True)
            else:
                embed.add_field(name='End:', value='No endtime found\n', inline=True)

            # Description & searching for image
            desc_str = eventdata[3][evtdtlistlen]
            if desc_str != None:
                invaludurl_warning_str = ''
                if 'image: ' in desc_str:
                    result = re.search(r'image: <a href="(.*)">(.*)</a>', desc_str)
                    img_url = result.group(1)
                    desc_str = re.sub(r'<b>|<br>|</b>|<a href=.*/a>|&nbsp;', '', desc_str)

                    # discord.py doesnt accept empty strings
                    if desc_str == '':
                        desc_str = 'No Description found.'

                    try:
                        embed.set_image(url=img_url)
                    except:
                        invaludurl_warning_str = 'Invalid url given! Have you formattet it as described in [help]?'

                embed.add_field(name='Description:', value=f'{desc_str}\n{invaludurl_warning_str}', inline=False)  

            else: embed.add_field(name='Description:', value='No Description found.', inline=False)
                
            await nchannel.send(embed=embed)
                        
        


    async def notify_guild_owner(self, message, **channelid):
        channel = await self.get_channel(channelid)
        guild = channel.guild()
        gowner = guild.owner()
        gowner.send('message')

    def google_api_get_events(self, timeframe, google_calendar_id):
        events = {}
        
        now = datetime.datetime.utcnow()                               # requests to the api must be made in UTC format
        time_nextcheck = now + datetime.timedelta(hours=timeframe, minutes=1)

        scopes = ['https://www.googleapis.com/auth/calendar.readonly']#.readonly'] # basically permissions needed from the user
        service_account_file = 'D:\\Dateien\\Programmieren\\Python\\ZeroBot\\zerobot-gcal-extension-serviceaccount-creds.json'
        credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        api_service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials, cache_discovery=False)
        api_response = api_service.events().list(calendarId=google_calendar_id,
                                                timeMin=now.isoformat() + 'Z',              # Formatted to match api requirements. 'Z' indicates UTC time
                                                timeMax=time_nextcheck.isoformat() + 'Z',   # Formatted to match api requirements. 'Z' indicates UTC time
                                                singleEvents=True,
                                                orderBy='startTime').execute()
        events = api_response.get('items', [])

        # returns the time the function was started, the timeframe which the function was given, and the events gathered within that timeframe
        return events

    def google_apiresponse_sorter(self, events):
        google_apiresponse_start = []
        google_apiresponse_end = []
        google_apiresponse_summary = []
        google_apiresponse_description = []

        for event in events:
            # eventstart
            try:
                start = event['start'].get('dateTime', event['start'].get('date'))
                google_apiresponse_start.append(start)    
            except KeyError:
                google_apiresponse_start.append(None)
            # event expiration
            try:
                start = event['end'].get('dateTime', event['end'].get('date'))
                google_apiresponse_end.append(start)    
            except KeyError:
                google_apiresponse_end.append(None)
            # event summary (Title)
            try:
                google_apiresponse_summary.append(event['summary'])
            except KeyError:
                google_apiresponse_summary.append(None)    
            # event description
            try:
                google_apiresponse_description.append(event['description'])
            except KeyError:
                google_apiresponse_description.append(None)
        
        return google_apiresponse_start, google_apiresponse_end, google_apiresponse_summary, google_apiresponse_description

    def date_parser(self, input_str, format_reversed):
        if format_reversed == 0:
            date = input_str[:10]
        else:
            year = input_str[:4]
            month = input_str[5:7]
            day = input_str[8:10]
            date = f'{day}/{month}/{year}'
        time = input_str[11:16]
        return f'{date} {time}'




def setup(bot):
    bot.add_cog(GooglecalendarExtension(bot))