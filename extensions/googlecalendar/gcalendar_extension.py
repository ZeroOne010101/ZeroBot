from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from SECRETS import gcal_caladdr, gcal_notifi_channel

import discord
from discord.ext import commands, tasks



# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def setup(bot):
    bot.add_cog(gcalendar(bot))

class gcalendar(commands.Cog):
    def __init__(self, bot, gcal_notifi_channel, gcal_caladdr):
        self.bot = bot
        self.notifi_channel = gcal_notifi_channel
        self.events = {}
        self.get_gcal_events.start()

    @tasks.loop(minutes= 30)
    async def get_gcal_events(self):
        
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now_gcalstring = datetime.datetime.now().isoformat() + 'Z' # 'Z' indicates UTC time
        

        events_result = service.events().list(calendarId=gcal_caladdr, timeMin=now_gcalstring,
                                            maxResults=1, singleEvents=True,
                                            orderBy='startTime').execute()
        
        self.events = events_result.get('items', [])
        print('getting events')

    @commands.command()
    async def botoutput(self, ctx):
        if not self.events:
            print('No Events found')
        else:
            for event in self.events:
                self.event_summary = event.get('summary' , 'No title available')
                self.event_description = event.get('description' , 'No description available')
                self.event_location = event.get('location' , 'No location available')
                self.event_starttime_str = event['start'].get('dateTime' , 'No starttime available')
                self.event_endtime_str = event['end'].get('dateTime' , 'No end available')
                #sending message
                ch = self.bot.get_channel(self.notifi_channel)
                await ch.send( '```' + '\n' + self.event_summary + '\n' + self.event_description + '\n' + self.event_location + '\n' + self.event_starttime_str + '\n' + self.event_endtime_str + '```')
    


    





