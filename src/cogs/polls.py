from discord import Embed
from discord.ext import tasks, commands
import logging
import pathlib
import re
from datetime import date, timedelta
from asyncpg import PostgresError
import traceback
from emoji import UNICODE_EMOJI
from __main__ import path, dbPool

##### Exceptions #####
class PollsBaseException(commands.CommandError):
    """Base exception for all poll exceptions"""
    pass
class InvalidEmojiError(PollsBaseException):
    def __init__(self, emoji):
        self.emoji = emoji
class ChannelNotFoundException(PollsBaseException):
    """Exception that occurs when the channel specified by the caller is not found"""
    def __init__(self, channelId):
        self.channelId = channelId

class ChannelNotInGuildException(PollsBaseException):
    """Exception that occurs when the channel specified by the caller does not match with the context guild"""
    def __init__(self, guildId: int, channelId: int, matchedChannelId: int):
        self.guildId = guildId
        self.channelId = channelId
        self.matchedChannelId = matchedChannelId

class NoOptionsException(PollsBaseException):
    """Exception that occurs when the caller does not specify any options"""
    def __init__(self, guildId: int, channelId: int):
        self.guildId = guildId
        self.channelId = channelId

##### Classes #####
class PollOption:
    """Dataclass defining a single pollOption"""
    def __init__(self, option: str, reaction: str, responses: int, responders: list, optionId=None):
        self.optionId = optionId
        self.option = option
        self.reaction = reaction
        self.responses = responses
        self.responders = responders

class Poll:
    """Class defining the Poll object"""
    def __init__(self):
        self.pollId = None
        self.guildId: int = None
        self.channelId: int = None
        self.messageId: int = None
        self.messageTitle: str = None
        self.verbose: bool = False
        self.options: list = []
        self.creationDate = None

    @classmethod
    async def from_db(cls, bot: commands.Bot, pollId: int):
        """Creates a Poll object from the db using the poll id"""
        # Creates Poll object using classmethod placeholder
        poll = cls()
        try:
            async with dbPool.acquire() as conn:
                # Query the polls database
                pollQueryResults = await conn.fetchrow('SELECT * FROM polls WHERE id = $1;', pollId) # Returns Record object of row
                # Initializes poll using the values from the database & option object
                poll.pollId = pollId
                pollChannel = bot.get_channel(pollQueryResults['channel_id'])
                poll.guildId = pollChannel.guild.id
                poll.channelId = pollQueryResults['channel_id']
                poll.messageId = pollQueryResults['message_id']
                poll.messageTitle = pollQueryResults['title']
                poll.verbose = bool(pollQueryResults['verbose'])
                poll.options = []
                poll.creationDate = pollQueryResults['creation_date']

                # Query the poll_options database
                pollOptionsQueryResults = await conn.fetch('SELECT * FROM poll_options WHERE fk = $1;', pollId) # Returns list of Records
                for pollOptionsRecord in pollOptionsQueryResults:
                    optionObject = PollOption(pollOptionsRecord['option'], pollOptionsRecord['reaction'], pollOptionsRecord['responses'], [], optionId=pollOptionsRecord['id'])

                    # Query the poll_responders database for each option
                    pollRespondersQueryResults = await conn.fetch('SELECT * FROM poll_responders WHERE fk = $1;', pollOptionsRecord["id"]) # Returns list of Records
                    # Add the responder id's to the options object
                    for pollRespondersRecord in pollRespondersQueryResults:
                        optionObject.responders.append(pollRespondersRecord['responder_id'])
                    # Add the options object to the poll object
                    poll.options.append(optionObject)
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        return poll

    async def update_db(self):
        """Updates the database using the poll's data"""
        try:
            async with dbPool.acquire() as conn:
                async with conn.transaction():
                    ## Update poll table
                    await conn.execute('UPDATE polls SET message_id = $1, title = $2, \"verbose\" = $3, channel_id = $4 WHERE id = $5;', self.messageId, self.messageTitle, self.verbose, self.channelId, self.pollId)
                    ## Update poll_options table
                    for option in self.options:
                        await conn.execute('UPDATE poll_options SET option = $1, reaction = $2, responses = $3 WHERE id = $4;', option.option, option.reaction, option.responses, option.optionId)
                        ## Update poll_responders table
                        # Get list of records of existing responders from db
                        responderRecords = await conn.fetch('SELECT responder_id FROM poll_responders WHERE fk = $1', option.optionId)
                        # Convert into list of existing responders
                        responderList = []
                        for responderRecord in responderRecords:
                            responderList.append(responderRecord['responder_id'])
                        # Add new responders to db
                        for responderId in option.responders:
                            if responderId not in responderList:
                                await conn.execute('INSERT INTO poll_responders(fk, responder_id) VALUES($1, $2);', option.optionId, responderId)
                        # Remove deleted/missing responders from db
                        for responderId in responderList:
                            if responderId not in option.responders:
                                await conn.execute('DELETE FROM poll_responders WHERE fk = $1 AND responder_id = $2', option.optionId, responderId)
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error

    async def to_db(self):
        """Inserts a new poll into the database"""
        try:
            async with dbPool.acquire() as conn:
                async with conn.transaction():
                    dbGuildId = await conn.fetchval('SELECT id FROM guilds WHERE guild_id = $1;', self.guildId)
                    await conn.execute('INSERT INTO polls(fk, message_id, title, \"verbose\", channel_id, creation_date) VALUES($1, $2, $3, $4, $5, $6);', dbGuildId, self.messageId, self.messageTitle, self.verbose, self.channelId, date.today())
                    dbPollId = await conn.fetchval('SELECT id FROM polls WHERE message_id = $1;', self.messageId)
                    for option in self.options:
                        await conn.execute('INSERT INTO poll_options(fk, option, reaction, responses) VALUES($1, $2, $3, $4);', dbPollId, option.option, option.reaction, option.responses)
                        dbOptionId = await conn.fetchval('SELECT id FROM poll_options WHERE fk = $1 AND option = $2;', dbPollId, option.option)
                        for responder in option.responders:
                            await conn.execute('INSERT INTO poll_responders(fk, responder_id) VALUES($1, $2);', dbOptionId, responder)
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error

    @classmethod
    def from_input(cls, bot: commands.Bot, ctx: commands.Context, input: str):
        """Creates a Poll object from user input and invocation context"""
        # Creates object from classmethod placeholder
        poll = cls()
        # Verbosity
        verboseMatch = re.search(r'verbose\s?=\s?(true|yes)', input)
        if verboseMatch != None:
            if verboseMatch.group(1) in ['true', 'yes'] :
                poll.verbose = True
        
        # Guild id
        poll.guildId = ctx.guild.id

        # Channel id
        poll.channelId = ctx.channel.id
        chIdMatch = re.search(r'channelid\s?=\s?([0123456789]*)', input)
        if chIdMatch != None:
            matchedId = int(chIdMatch.group(1))
            matchedChannel = bot.get_channel(matchedId)
            if matchedChannel is None:
                raise ChannelNotFoundException(matchedId)
            matchedGuild = matchedChannel.guild
            if ctx.guild == matchedGuild:
                poll.guildId = ctx.guild.id
                poll.channelId = matchedId
            else:
                raise ChannelNotInGuildException(ctx.guild.id, ctx.channel.id, matchedId)

        # Reactions & options
        optMatch = re.search(r'options\s?=\s?\[(.*)\]', input, re.DOTALL)
        if optMatch != None:
            if optMatch.group(1) != '':
                optMatchList = re.findall(r'\s*(\S|[^;]+?)\s*\|\s*([^;\s]+)\s*', optMatch.group(1))
                for option, reaction in optMatchList:
                    if reaction in UNICODE_EMOJI or not re.match(r'<a?:\w*:\d*>', reaction) is None:
                        poll.options.append(PollOption(option, reaction, 0, []))
                    else:
                        raise InvalidEmojiError(reaction)
            else:
                raise NoOptionsException(ctx.guild.id, ctx.channel.id)
        else:
            raise NoOptionsException(ctx.guild.id, ctx.channel.id)

        # Message title
        poll.messageTitle = 'No title specified'
        titleMatch = re.search(r'title\s?=\s?\'(.*)\'', input, re.DOTALL)
        if titleMatch != None:
            if titleMatch.group(1) != '':
                poll.messageTitle = titleMatch.group(1)

        return poll

class PollsCog(commands.Cog):
    """The Cog object that gets loaded by the bot"""
    def __init__(self, bot):
        self.bot = bot
        self.dbCleaner.start()

    async def constructEmbed(self, poll: Poll):
        embed = Embed(title=poll.messageTitle)
        for option in poll.options:
            responseStr = '-----'
            if option.responses != 0:
                responseStr = ''
                if poll.verbose:
                    for responderId in option.responders:
                        user = self.bot.get_user(responderId)
                        responseStr += f'{user.display_name}\n'
                else:
                    responseStr = str(option.responses)
            embed.add_field(name=option.option, value=responseStr, inline=False)
        return embed

    @commands.guild_only()
    @commands.command(name='poll')
    async def pollCommand(self, ctx: commands.Context, *, args: str):
        poll = Poll.from_input(self.bot, ctx, args)
        pollEmbed = await self.constructEmbed(poll)
        msgChannel = self.bot.get_channel(poll.channelId)
        message = await msgChannel.send(embed=pollEmbed)
        poll.messageId = message.id
        # Add corresponding reactions to the message
        for option in poll.options:
            await message.add_reaction(option.reaction)
        # Commit the created poll to the database
        await poll.to_db()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        """Called whenever a reaction is added to a message"""
        # Prevent from acting on bot reactions
        user = self.bot.get_user(reaction.user_id)
        if user.bot: return
        # Convert partial emoji to string
        emoji = reaction.emoji
        if emoji.is_unicode_emoji():
            emoji = emoji.name
        elif emoji.is_custom_emoji():
            emoji = self.bot.get_emoji(emoji.id)
            if emoji.animated:
                emoji = f'a<:{emoji.name}:{emoji.id}>'
            else:
                emoji = f'<:{emoji.name}:{emoji.id}>'
        # Match the message being reacted to to the database
        try:
            async with dbPool.acquire() as conn:
                dbPollId = await conn.fetchval('SELECT id FROM polls WHERE message_id = $1;', reaction.message_id)
                if not dbPollId is None:
                    # Create poll from message id
                    poll = await Poll.from_db(self.bot, dbPollId)
                    for option in poll.options:
                        if option.reaction == emoji:
                            option.responses += 1
                            option.responders.append(reaction.user_id)
                    await poll.update_db()
                    msgChannel = self.bot.get_channel(poll.channelId)
                    message = await msgChannel.fetch_message(poll.messageId)
                    await message.edit(embed = await self.constructEmbed(poll))
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction): 
        """Called whenever a reaction is removed from a message"""
        # Prevent from acting on bot reactions
        user = self.bot.get_user(reaction.user_id)
        if user.bot: return
        # Convert partial emoji to string
        emoji = reaction.emoji
        if emoji.is_unicode_emoji():
            emoji = emoji.name
        elif emoji.is_custom_emoji():
            emoji = self.bot.get_emoji(emoji.id)
            if emoji.animated:
                emoji = f'<a:{emoji.name}:{emoji.id}>'
            else:
                emoji = f'<:{emoji.name}:{emoji.id}>'
        # Match the message the reaction was removed from to the database
        try:
            async with dbPool.acquire() as conn:
                dbPollId = await conn.fetchval('SELECT id FROM polls WHERE message_id = $1 AND channel_id = $2;', reaction.message_id, reaction.channel_id)
                if not dbPollId is None:
                    # Create poll from message id
                    poll = await Poll.from_db(self.bot, dbPollId)
                    for option in poll.options:
                        if option.reaction == emoji:
                            option.responses -= 1
                            option.responders.remove(reaction.user_id)
                    await poll.update_db()
                    msgChannel = self.bot.get_channel(poll.channelId)
                    message = await msgChannel.fetch_message(poll.messageId)
                    await message.edit(embed = await self.constructEmbed(poll))
                else:
                    raise PollsBaseException(reaction.guildId, reaction.channelId)
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
    
    def cog_unload(self):
        """Cancels tasks if the cog gets unloaded"""
        self.dbCleaner.cancel()

    @tasks.loop(hours=24)
    async def dbCleaner(self):
        """Task that removes polls older than 4 weeks from the database"""
        logging.info('Task dbCleaner has started.')
        now = date.today()
        try:
            async with dbPool.acquire() as conn:
                dbPollRecords = await conn.fetch('SELECT * FROM polls;')
                for dbPollrecord in dbPollRecords:
                    if now - timedelta(weeks=4) > dbPollrecord['creation_date']:
                        async with conn.transaction():
                            await conn.execute('DELETE FROM polls WHERE id = $1', dbPollrecord['id'])
        except PostgresError as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error
        except Exception as error:
            logging.error(f'{error.__class__.__name__}: {error}')
            raise error

        logging.info('Task dbCleaner has ended.')

    @dbCleaner.before_loop
    async def before_dbCleaner(self):
        """Makes sure that the bot is ready before the task is started"""
        await self.bot.wait_until_ready()

    ##### Error handling #####
    @pollCommand.error
    async def pollCommandErrorhandler (self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            logging.info(f"Ignoring exception {error.__class__.__name__} in command {ctx.command}")
            await ctx.send(f'```At least one option needs to be specified for this command```')
        elif isinstance(error, NoOptionsException):
            logging.info(f"Ignoring exception {error.__class__.__name__} in command {ctx.command}")
            await ctx.send(f'```At least one option needs to be specified to create a poll```')
        elif isinstance(error, ChannelNotFoundException):
            logging.info(f"Ignoring exception {error.__class__.__name__} in command {ctx.command}")
            await ctx.send(f"```The channel id you specified could not be found\nThis error is usually caused because the bot is not part of the guild/server```")
        elif isinstance(error, ChannelNotInGuildException):
            logging.info(f"Ignoring exception {error.__class__.__name__} in command {ctx.command}")
            await ctx.send(f'```The channel id you specified is not part of the guild/server you are issuing the command from```')
        elif isinstance(error, InvalidEmojiError):
            logging.info(f"Ignoring exception {error.__class__.__name__} in command {ctx.command}")
            await ctx.send(f'```The emoji \"{error.emoji}\" you specified does not seem to be valid.\nPlease contact the owner if that is not the case```')
        else:
            logging.info(f"Ignoring exception {error.__class__.__name__} in command {ctx.command}")
            raise error


def setup(bot):
    bot.add_cog(PollsCog(bot))