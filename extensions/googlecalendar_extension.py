import discord
from discord.ext import tasks, commands

import googleapiclient.discovery
from google.oauth2 import service_account

import datetime
import os
import aiosqlite
import asyncio

class GcalEvent:
    def __init__(self, event):
        self.start = None
        self.end = None
        self.title = None
        self.description = None
        # parse the api response into the event attributes
        self._eventparse(event)
        # parse any triggers
        self.botinfo = GcalBotInfo(self.description)
    
    def _eventparse(self, event):
        # start
        try:
            start = event['start'].get('dateTime', event['start'].get('date'))
            self.start = start 
        except KeyError:
            pass
        
        # end
        try:
            end = event['end'].get('dateTime', event['end'].get('date'))
            self.end = end
        except KeyError:
            pass
        
        # event summary (Title)
        try:
            self.title = event['summary'])
        except KeyError:
            pass
        
        # event description
        try:
            self.description= event['description']
        except KeyError:
            pass
        
class GcalBotInfo:
    def __init__(self, description):
        self.remind = False
        self.pollcmd = None
        
        self._parsedesc(description)
        
    def self._parsedesc(self, description):
        pass

def get_events(temeframe, calid):
    events = {}
        
    now = datetime.datetime.utcnow() # requests to the api must be made in UTC format
    time_nextcheck = now + datetime.timedelta(hours=timeframe, minutes=1) # +1 minute to account for latency.

    scopes = ['https://www.googleapis.com/auth/calendar.readonly'] # basically permissions needed from the user
    # TODO: update to pathlib
    service_account_file = "D:\\Dateien\\Programmieren\\Python\\ZeroBot\\zerobot-gcal-extension-serviceaccount-creds.json"
    credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    api_service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
    
    api_response = api_service.events().list(calendarId=google_calendar_id,
                                                # Formatted to match api requirements. 'Z' indicates UTC time
                                                timeMin=now.isoformat() + 'Z',
                                                # Formatted to match api requirements. 'Z' indicates UTC time
                                                timeMax=time_nextcheck.isoformat() + 'Z',
                                                singleEvents=True,
                                                orderBy='startTime').execute()
    events = api_response.get('items', [])
    return events

def buildEmbed(event):
    pass






### LEGACY BELOW ###











# ToDo: - make this compatible with the db and multiple guilds(attach guild id to output list?)
#       - find out how to give guilds the ability to set custom parameters(aka find out how to get the reminder time from google)
#       - bind functionality to tags. eg:[inage]
#       - parse image: url in the description, complete with error handling
#       - Find out if adding the service account to private calendars works. Else, issue instructions accordingly

os.chdir('D:\\Dateien\\Programmieren\\Python\\ZeroBot')

class googlecalendar_extension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.gcal_notifier())
    
    async def gcal_notifier(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            async with aiosqlite.connect('D:\\Dateien\\Programmieren\\Python\\ZeroBot\\ZeroBot_db.sqlite') as db:
                calendar_dbdata =  await db.execute('SELECT gcal_calendar_id, gcal_notification_channel, format_reversed FROM gcal_ext;')
                calendar_dbdata = await calendar_dbdata.fetchall()
            for dbdata in calendar_dbdata:
                # abstracting database calls
                calendar_adress = dbdata[0]
                nchannel_id = dbdata[1]
                nchannel = self.bot.get_channel(nchannel_id)
                format_reversed = dbdata[2]
                
                eventdata = self.google_apiresponse_sorter(self.google_api_get_events(168, calendar_adress)) # ToDo: add try: except to it so id doesnt break on every invalid calendar address, and notify the guild owner (maybe: run this in executor so the bot doesnt slow down)
                
                # get all bot-messages in nchannel
                messages_to_delete = []
                async for message in nchannel.history(limit=100):
                    if message.author == self.bot.user:
                        messages_to_delete.append(message)
                # delete all messages in list
                try:
                    await nchannel.delete_messages(messages_to_delete)
                except ClientException:
                    pass # logging here, this occurs when more than 100 messages get deleted
                except Forbidden:
                    pass # logging here, occurs when the permissions dont fit
                except HTTPException:
                    pass # logging here, occurs when deleting the messages failed

                # loop thruogh the 0'th list with evtdtelementlen being the current list-element
                # TODO: this is not perfict, in the future use the longest list in eventdata
                for i in range(len(eventdata[0])):
                    # further abstracting eventdata calls
                    evt_starttime = eventdata[0][i]
                    evt_endtime = eventdata[1][i]
                    evt_title = eventdata[2][i]
                    evt_description = eventdata[3][i]
                    
                    # Title
                    if evt_title != None:
                        embed = discord.Embed(title=evt_title)
                        # print(eventdata[2][evtdtlistlen])
                    else:
                        embed = discord.Embed(title='No Title Found')
                        
                    # Starttime
                    if evt_starttime != None:
                        # plug starttime into parser
                        eventdata_start = self.date_parser(evt_starttime, format_reversed)
                        # add parsed string to embed
                        embed.add_field(name='Start:', value=f'{eventdata_start}\n', inline=True)
                    else:
                        embed.add_field(name='Start:', value='No starttime found\n', inline=True)

                    # Endtime
                    if evt_endtime != None:
                        eventdata_end = self.date_parser(evt_endtime, format_reversed)
                        embed.add_field(name='End:', value=f'{eventdata_end}\n', inline=True)
                    else:
                        embed.add_field(name='End:', value='No endtime found\n', inline=True)

                    # Description & searching for image
                    # TODO: make the parsing a function for readability! also do something about the repetitive structure!
                    if evt_description != None:
                        # string to send when invalid url is passed, may become obsolete after error handling is done
                        invaludurl_warning_str = ''
                        # Splits the string into a list at every whitespace
                        evt_description_str_list = evt_description.split()
                        for element in evt_description_str_list:
                            if 'image:' in element and element != 'image:':
                                img_url = element.replace('image:', '')
                                evt_description = evt_description.replace(element, '')
                                # discord.py doesnt accept empty strings
                                if evt_description == '':
                                    evt_description = 'No Description found.'

                                try:
                                    embed.set_image(url=img_url)
                                except:
                                    invaludurl_warning_str = 'Invalid url given!'
                            elif element == 'image:':
                                img_url = evt_description_str_list[evt_description_str_list.index('image:')+1]
                                evt_description = evt_description.replace(f'image: {img_url}', '')
                                # discord.py doesnt accept empty strings
                                if evt_description == '':
                                    evt_description = 'No Description found.'

                                try:
                                    embed.set_image(url=img_url)
                                except:
                                    invaludurl_warning_str = 'Invalid url given!'
                        embed.add_field(name='Description:', value=f'{evt_description}\n{invaludurl_warning_str}', inline=False)
                        
                    else:
                        embed.add_field(name='Description:', value='No Description found.', inline=False)

                    await nchannel.send(embed=embed)
                        
                    # possibly add logging here for what gets sent where

            await asyncio.sleep(2*60*60)

    def google_api_get_events(self, timeframe, google_calendar_id):
        events = {}
        
        now = datetime.datetime.utcnow()                               # requests to the api must be made in UTC format
        time_nextcheck = now + datetime.timedelta(hours=timeframe, minutes=1)

        scopes = ['https://www.googleapis.com/auth/calendar.readonly']#.readonly'] # basically permissions needed from the user
        service_account_file = 'D:\\Dateien\\Programmieren\\Python\\ZeroBot\\zerobot-gcal-extension-serviceaccount-creds.json'
        credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        api_service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
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
    bot.add_cog(googlecalendar_extension(bot))
