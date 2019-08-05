import discord
from discord.ext import commands

import re
import logging

class ReactCounter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactdict = { 
            'guild_ids':[],
            'msg_ids':[],
            'msg_titles':[],
            'verbose':[],
            'reactnames':[],
            'reacts':[],
            'responses':[]
            }
    
    # REMEMBER TO REMOVE
    @commands.command()
    async def listdict(self, ctx):
        await ctx.send(str(self.reactdict))

    @commands.command(name='poll')
    async def createrc (self, ctx, *, optargs=''):
        # Note: the current way of doing things possibly isnt best practice, see notes in parsetest.py
        if optargs == '':
            ctx.send('ERROR: No arguments were passed!')
        ##### parsing optargs #####
        # parsing verboseness
        verbose_match = re.search(r'verbose=(True)', optargs)
        if verbose_match != None:
            if verbose_match.group(1) == 'True':
                verbose = True
            else:
                verbose = False
        else:
            verbose = False

        # parsing and getting the channel and guild for sending the message and adding the guild to the dict
        chid_match = re.search(r'channelid=([0123456789]*)', optargs)
        if chid_match != None:
            channel_id = int(chid_match.group(1))
            if ctx.guild == self.bot.get_channel(channel_id).guild:
                try:
                    channel = self.bot.get_channel(channel_id)
                    guild_id = ctx.guild.id
                except:
                    await ctx.send('Could not get channel.')
                    return
            else:
                await ctx.send('The specified Channel is not part of the server you are in.')
                return
        else:
            channel = ctx.channel
            guild_id = ctx.guild.id

        # parsing reactions
        # TODO: check if reactions are identical, and throw an error message if they are # but maybe dont, this could enable groups
        react_match = re.search(r'reactions=\[(.*)\]', optargs)
        logging.debug(f'type:{type(optargs)} input:{optargs}')
        if react_match != None:
            react_match = react_match.group(1)
            if react_match != '':
                react_list = re.findall(r'(\S*)\|(\S*)', react_match)

                # deconstructing the tuple and reconstructing it as list, so it can be changed
                old_list = react_list
                react_list = []
                for item in old_list:
                    # contents of tuple
                    tcont_0 = item[0]
                    tcont_1 = item[1]
                    appendlist = [tcont_0, tcont_1]
                    react_list.append(appendlist)

                # extracting and saving the ids of custom emojis
                for lst in react_list:
                    item_match = re.match(r'<a?:.*:(.*)>', lst[1])
                    if item_match != None:
                        lst[1] = int(item_match.group(1))
                
            else:
                ctx.send('ERROR: Empty brackets were passed.')
                return
        else:
            await ctx.send('ERROR: No reaction argument was passed.')
            return

        # parsing msgtitle
        title_match = re.search(r'title=\'(.*)\'', optargs)
        if title_match != None:
            msg_title = title_match.group(1)
            if msg_title == '':
                msg_title = 'No Title Specified'
        else: msg_title = 'No Title Specified'

        ##### adding parsed (and non parsed) stuff to the dict #####
        # adding guild-id, message title and verboseness to the dict
        dictarguments = ['guild_ids', 'msg_titles', 'verbose']
        items = [guild_id, msg_title, verbose]
        for i in range(len(dictarguments)):
            self.reactdict[dictarguments[i]].append(items[i])
        
        # adding the reactions to the dict
        rnameslist = []
        reactlist = []
        ritemlist = []
        for reactpair in react_list:
            reactname = reactpair[0]
            reaction = reactpair[1]
            rnameslist.append(reactname)
            reactlist.append(reaction)
            if verbose:
                ritemlist.append([])
            else:
                ritemlist.append(0)
        self.reactdict['reactnames'].append(rnameslist)
        self.reactdict['reacts'].append(reactlist)
        self.reactdict['responses'].append(ritemlist)

        # making and sending the embed
        embed = discord.Embed(title=msg_title) # initialising embed
        for rname in rnameslist:
            embed.add_field(name=rname, value='-----', inline=False)
        sent_message = await channel.send(embed=embed) # getting the message object from the sent message
        # adding id of sent message to dict
        self.reactdict['msg_ids'].append(sent_message.id)
        for reaction in reactlist:
            try:
                if type(reaction) == int:
                    await sent_message.add_reaction(self.bot.get_emoji(reaction))
                else:
                    await sent_message.add_reaction(reaction)
            except:
                await ctx.send(f'```ERROR: Reaction/Emoji ({reaction}) is not supported or reaction is not a reaction.\nPlease make sure that your reaction follows the :reaction: format.\nOther formats may work in discord, but are not supported.```')
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):   # Note: this event will only trigger if the message is in the messagecache.
        # return if the message is not registered in the dict and therefore another message from the bot, or if the one reacting is a bot
        if reaction.message.id not in self.reactdict['msg_ids'] or user.bot:
            return

        # find index of referenced reactioncounter message via the message id, use that index to get the index of the reaction
        msg_index = self.reactdict['msg_ids'].index(reaction.message.id)

        # return if the reacted emoji is not one marked for listening
        if reaction.emoji not in self.reactdict['reacts'][msg_index]:
            if type(reaction.emoji) == str:
                return
            elif reaction.emoji.id not in self.reactdict['reacts'][msg_index]:
                return

        # get verboseness
        verbose = self.reactdict['verbose'][msg_index]

        if reaction.custom_emoji:
            react_index = self.reactdict['reacts'][msg_index].index(reaction.emoji.id)
        else:
            react_index = self.reactdict['reacts'][msg_index].index(reaction.emoji)
        
        if not verbose:
            self.reactdict['responses'][msg_index][react_index] += 1
        else:
            self.reactdict['responses'][msg_index][react_index].append((user.name, user.id))
        
        # getting stuff from dict to construct new embed to replace the original with
        msg_title = self.reactdict['msg_titles'][msg_index]
        reactnames = self.reactdict['reactnames'][msg_index]
        responses = self.reactdict['responses'][msg_index]
        
        # constructing embed to replace the original with
        embed = discord.Embed(title=msg_title)
        for i in range(len(reactnames)):
            rname = reactnames[i]
            if verbose and len(responses) <= 0:
                response = '-----'
            elif verbose:
                response = ''
                for responseitem in responses[i]:
                    print(responses)
                    print(i)
                    print(responseitem[0])
                    response = response + f'{responseitem[0]} '
                if response == '':
                    response = '-----'
            else:
                response = str(responses[i])
            embed.add_field(name=rname, value=response, inline=False)

        
        # sending the embed
        message = reaction.message
        await message.edit(embed=embed)
        logging.info('on_reaction_add completed')

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):   # Note: this event will only trigger if the message is in the messagecache.
        # return if the message is not registered in the dict and therefore another message from the bot, or if the one reacting is a bot
        if reaction.message.id not in self.reactdict['msg_ids'] or user.bot:
            return
        
        # find index of referenced reactioncounter message via the message id, use that index to get the index of the reaction
        msg_index = self.reactdict['msg_ids'].index(reaction.message.id)

        # return if the reacted emoji is not one marked for listening
        if reaction.emoji not in self.reactdict['reacts'][msg_index]:
            if type(reaction.emoji) == str:
                return
            elif reaction.emoji.id not in self.reactdict['reacts'][msg_index]:
                return

        # get verboseness
        verbose = self.reactdict['verbose'][msg_index]

        if reaction.custom_emoji:
            react_index = self.reactdict['reacts'][msg_index].index(reaction.emoji.id)
        else:
            react_index = self.reactdict['reacts'][msg_index].index(reaction.emoji)
        
        if not verbose:
            self.reactdict['responses'][msg_index][react_index] -= 1
        else:
            self.reactdict['responses'][msg_index][react_index].remove((user.name, user.id))
        
        # getting stuff from dict to construct new embed to replace the original with
        msg_title = self.reactdict['msg_titles'][msg_index]
        reactnames = self.reactdict['reactnames'][msg_index]
        responses = self.reactdict['responses'][msg_index]

        # constructing embed to replace the original with
        embed = discord.Embed(title=msg_title)
        for i in range(len(reactnames)):
            rname = reactnames[i]
            if verbose and len(responses) <= 0:
                response = '-----'
            elif verbose:
                response = ''
                for responseitem in responses[i]:
                    print(responses)
                    print(i)
                    print(responseitem[0])
                    response = response + f'{responseitem[0]} '
                if response == '':
                    response = '-----'
            else:
                response = str(responses[i])
            embed.add_field(name=rname, value=response, inline=False)
        
        # sending the embed
        message = reaction.message
        await message.edit(embed=embed)
        logging.info('on_reaction_remove completed')

def setup(bot):
    bot.add_cog(ReactCounter(bot))
