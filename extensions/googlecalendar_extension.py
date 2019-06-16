import discord
from discord.ext import commands

import googleapiclient.discovery
from google.oauth2 import service_account

import datetime
import functools
import os


# ToDo: - make this compatible with the db and multiple guilds(attach guild id to output list?)
#       - find out how to give guilds the ability to set custom parameters(aka find out how to get the reminder time from google)
#       - bind functionality to tags.
#       - parse image: url in the description, complete with error handling

os.chdir('D:\\Dateien\\Programmieren\\Python\\ZeroBot')

#
# Google API request functions
#

def google_api_get_events(timeframe, google_calendar_id):
    events = {}
    
    now = datetime.datetime.now()
    time_nextcheck = now + datetime.timedelta(minutes=timeframe+1)

    scopes = ['https://www.googleapis.com/auth/calendar.readonly'] # basically permissions needed from the user
    service_account_file = 'D:\\Dateien\\Programmieren\\Python\\ZeroBot\\zerobot-gcal-extension-service-acc-creds.json'
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

    

def google_apiresponse_sorter(events):
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

def googlecalendar_function(timeframe, google_calendar_id):
    events = google_api_get_events(timeframe, google_calendar_id)
    returnpassthrough = google_apiresponse_sorter(events)
    return returnpassthrough

class googlecalendar_extension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.


def setup(bot):
    bot.add_cog(googlecalendar_extension(bot))