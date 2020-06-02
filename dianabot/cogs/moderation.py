import types
import logging
import discord
from discord.ext import commands
from dianabot.utils.aiopbwrap import AsyncPastebin
from dianabot.utils.misc import is_author, message_embed

log = logging.getLogger('discord')

class Moderation(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="makesay")
    @commands.has_permissions(administrator=True)
    async def make_say(self, ctx, dest: discord.TextChannel, *, message):  # pylint: disable=unused-argument
        await dest.send(content=message)

    @make_say.error
    async def makesay_error(self, error, ctx):
        if isinstance(error, commands.MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you're not a mod, so I don't have to listen to you!"
            await ctx.send(text)

    @commands.command(name="laogai")
    @commands.has_permissions(administrator=True)
    async def laogai(self, ctx, member: discord.Member, reason:str=None):
        laogai_role = ctx.guild.get_role(self.bot.config.laogai_id[ctx.guild.id])
        await member.add_roles(laogai_role,reason=reason)

    @laogai.error
    async def laogai_error(self, error, ctx):
        text = None
        if isinstance(error, commands.MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you're not a mod, so you can't do that!"
        elif isinstance(error, discord.Forbidden):
            text = "Sorry, I don't have permission to do that :pensive: A mod needs to give me the 'Manage Roles' permission."
        if text:
            await ctx.send(text)
    
    @commands.command(name="log")
    @commands.has_permissions(administrator=True)
    async def logchannel(self, ctx, channel: discord.TextChannel, name: str=None, limit: int=None, before=None, after=None):
        """
        use in the channel where you want the ultimate pastebin link to be posted
        requires bot to have read_message_history permissions
        """
        if self.bot.config.pastebin_dev_key is None: #need to implement this into config (since you need to rewrite config anyway)
            await ctx.send(
                "Sorry, I haven't been given a proper pastebin API dev key, so I can't take logs that way.")
        else:
            async with channel.typing():
                log_list = []
                log_list.append("==============================================================")
                log_list.append(f"Guild: {ctx.Guild.name}")
                if channel.category.name is None:
                    cat = " "
                else:
                    cat = channel.category.name + " / "
                log_list.append(f"Channel: {cat}{channel.name}")
                log_list.append("==============================================================")
                messages = await channel.history(oldest_first=True, limit=limit, before=before, after=after).flatten()
                for mess in messages:
                    log_list.append("")
                    log_list.append(f"[{mess.created_at}] {mess.author.name}#{mess.author.discriminator}")
                    log_list.append(f"{mess.content}")
                    if mess.edited_at:
                        log_list.append(f"(edited at {mess.edited_at})")
                    #if (reacts := mess.reactions):
                        #implement later
                textfile = "\n".join(log_list)
                pb = AsyncPastebin(self.bot.config.pastebin_dev_key)
                pasted_url = await pb.create_paste(textfile, api_paste_private=1, api_paste_name=name, api_paste_format="text")
                await ctx.send(pasted_url)

    @logchannel.error
    async def logchannel_error(self, error, ctx):
        text = None
        if isinstance(error, discord.Forbidden):
            text = "Sorry, I don't have permissions to get channel message history, so I'm unable to do that."
        elif isinstance(error, discord.HTTPException):
            text = "Sorry, something went wrong with Discord and my attempt to get the message history failed."
        if text:
            await ctx.send(text)
    
    @commands.group(name="nuke", brief="used to delete a large number of messages from a channel")
    @commands.has_permissions(administrator=True)
    async def nukechannel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("This command requires a subcommand...")

    @nukechannel.command(name="any", brief="deletes n most recent messages in channel")
    async def nuke_any(self, ctx, dest: discord.TextChannel, n: int=0):
        del_mes = await dest.purge(limit=n)
        await ctx.send("I deleted **{}** messages from #{}".format(len(del_mes),dest.name))

    @nukechannel.command(name="user", brief="deletes all messages from a given user within the n most recent messages")
    async def nuke_user(self, ctx, dest: discord.TextChannel, user: discord.User, n: int=0):
        user.is_author = types.MethodType(is_author, user)
        del_mes = await dest.purge(limit=n, check=user.is_author)
        await ctx.send("I deleted **{}** messages by {}#{} from #{}".format(len(del_mes),user.name,user.discriminator,dest.name))

    #@nukechannel.command(name="regex")
    #async def 
    #this will be hard, do it later

    #@nukechannel.command(name="all")
    #this might be impossible?

    @nukechannel.error
    async def nukechannel_error(self, error, ctx):
        if isinstance(error, discord.Forbidden):
            await ctx.send("Sorry, I need the manage_messages and read_message_history permissions to do that!")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Oh no! Something went wrong! Purging messages failed.")

class GreyList(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        content = message.content.lower()
        server = message.guild.id
        grey_list = self.bot.config.greylist[server]["all"]
        if message.channel.id in self.bot.config.greylist[server]:
            channel_greylist = self.bot.config.greylist[server][message.channel.id]
            grey_list.update(channel_greylist)
        for word in grey_list:
            if word in content:
                if grey_list[word] == True:
                    await self.bot.config.mod_notif_channel[server].send(
                        f"{self.bot.config.mod_role[server].mention}, {message.author.name}#{message.author.discriminator} said {word} in {message.channel}.", 
                        embed=message_embed(message)
                        )
                else:
                    await self.bot.config.mod_notif_channel[server].send(
                        f"Hey, {message.author.name}#{message.author.discriminator} said {word} in {message.channel}.", 
                        embed=message_embed(message)
                        )
        
        #add commands to add and remove items from the greylist (both universally and channel-specifically) as well as change pingability
        #but you should probably stop procrastinating on writing Config() before you do that.


def setup(bot):
    bot.add_cog(Moderation(bot))
    bot.add_cog(GreyList(bot))