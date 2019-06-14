import discord
from discord.ext import commands
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import functools
import os


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# ToDo: - make this compatible with the db and multiple guilds(attach guild id to output list?)
#       - find out how to give guilds the ability to set custom parameters(aka find out how to get the reminder time from google)
#       - bind functionality to tags.
#       - parse image: url in the description, complete with error handling

os.chdir('D:\\Dateien\\Programmieren\\Python\\ZeroBot')


def setup(bot):
    bot.add_cog(gcalendar_ext(bot))

class gcalendar_ext(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scopes = ['https://www.googleapis.com/auth/calendar.readonly'] # basically permissions needed from the user
        self.flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes=self.scopes)
        self.gcalauth_task_is_running = False # Workaround to not have the bot spawn a new possibly unresolved process
        self.events = {}
        
    
    def gcalauth_task(self):
        self.flow.run_local_server(open_browser=False)

    @commands.command()
    async def run_gcalauth_task(self, ctx, bot):
        await ctx.channel.send('Please open this url in your browser and authorise the bot:\nhttps://accounts.google.com/o/oauth2/auth?response_type=code&client_id=218532216115-7f3iqbod33k9mlrm924bcn78jfbr1o19.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly&state=lhrMEQmkeX5H2fam1sCIgf9wd0e4yQ&access_type=offline\n You may receiver a warning because the bot has not been tested by google. You can enable the bot anyway by clicking on \'advanced\' an then on \'open ZeroBot gcal_extension\'.\nIf no action is taken within 15 minutes, the command needs to be issued again for performance reasons.')
        gcalauth_task_partial = functools.partial(self.gcalauth_task)
        if self.gcalauth_task_is_running == False:
            self.gcalauth_task_is_running = True
            # executor in order to not block the bot
            await bot.loop.run_in_executor(None, gcalauth_task_partial)
            self.gcalauth_task_is_running = False
        else:
            print('Not executed, because: self.gcalauth_task_is_running = True')
    
    def get_gcal_events(self, gcaladdr): # This Function will get called by the output function with all the necessary parameters from the db.
        pass                        # Continue here tomorrow, bake in the db while you're at it. Design a programm flow beforehand.













# Im redoing this again, this time with a custom oauth2 flow and the new db in mind








# def _gcalauth_task(gcalauth_task_check=gcalauth_task_check):
#     if gcalauth_task_check == False:
#         gcalauth_task_check = True
#         flow.run_local_server(open_browser=False)               #doesnt work!!! find out how to do the gcalauth thing
#         gcalauth_task_check = False
#     else:
#         return

# @bot.command()
# async def gcalauth(ctx, gcalauth_task_check=gcalauth_task_check):
#     await ctx.channel.send('Please open this url in your browser and authorise the bot:\nhttps://accounts.google.com/o/oauth2/auth?response_type=code&client_id=218532216115-7f3iqbod33k9mlrm924bcn78jfbr1o19.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly&state=lhrMEQmkeX5H2fam1sCIgf9wd0e4yQ&access_type=offline\n You may receiver a warning because the bot has not been tested by google. You can enable the bot anyway by clicking on \'advanced\' an then on \'open ZeroBot gcal_extension\'.\nIf no action is taken within 15 minutes, the command needs to be issued again for performance reasons.')
#     gcalauth_task_partial = functools.partial(_gcalauth_task)
#     if gcalauth_task_check == False:
#         # executor in order to not block the bot
#         await bot.loop.run_in_executor(None, gcalauth_task_partial)
#         gcalauth_task_check = True
#     else:
#         print('gcalauth_task_check was true')


# class gcalendar(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#         self.notifi_channel = SECRETS_gcal.gcal_notifi_channel # make compatible with database
#         self.gcal_caladdr = SECRETS_gcal.gcal_caladdr # make compatible with database
#         self.events = {}
#         self.get_gcal_events.start()

#     @tasks.loop(minutes= 30)
#     async def get_gcal_events(self):
        
#         creds = None
#         # The file token.pickle stores the user's access and refresh tokens, and is
#         # created automatically when the authorization flow completes for the first time.

#         if os.path.exists('token.pickle'):
#             with open('token.pickle', 'rb') as token:
#                 creds = pickle.load(token)
#         # If there are no (valid) credentials available, let the user log in.
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 flow = InstalledAppFlow.from_client_secrets_file(
#                     'credentials.json', SCOPES)
#                 creds = flow.run_local_server()
#             # Save the credentials for the next run
#             with open('token.pickle', 'wb') as token:
#                 pickle.dump(creds, token)

#         service = build('calendar', 'v3', credentials=creds)

#         # Call the Calendar API
#         now_gcalstring = datetime.datetime.now().isoformat() + 'Z' # 'Z' indicates UTC time
        

#         events_result = service.events().list(calendarId=self.gcal_caladdr, timeMin=now_gcalstring,
#                                             maxResults=1, singleEvents=True,
#                                             orderBy='startTime').execute()
        
#         self.events = events_result.get('items', [])
#         print('getting events')

#     @commands.command()
#     async def botoutput(self, ctx):
#         if not self.events:
#             print('No Events found')
#         else:
#             for event in self.events:
#                 self.event_summary = event.get('summary' , 'No title available')
#                 self.event_description = event.get('description' , 'No description available')
#                 self.event_location = event.get('location' , 'No location available')
#                 self.event_starttime_str = event['start'].get('dateTime' , 'No starttime available')
#                 self.event_endtime_str = event['end'].get('dateTime' , 'No end available')
#                 #sending message
#                 ch = self.bot.get_channel(self.notifi_channel)
#                 await ch.send( f'```\n{self.event_summary}\n{self.event_description}\n{self.event_location}\n{self.event_starttime_str}\n{self.event_endtime_str}```')