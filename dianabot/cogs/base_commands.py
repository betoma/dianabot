import logging
import random
import time

import discord
from discord.ext import commands

from dianabot.utils import misc


log = logging.getLogger("discord")


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="perms")
    async def perms(self, ctx, user: discord.User):
        """
        Usage:
            {command_prefix}perms (@MentionedUser)

        Get the permissions of a mentioned user.
        """
        if user.id == self.bot.user.id:
            perms_message = f"I'm {self.bot.config.bot_name[ctx.guild.id]}! I'm a bot."
        else:
            if user == ctx.author:
                perms_message = "you are "
            else:
                perms_message = f"{user.name}#{user.discriminator} is "
            if user.id == int(self.bot.owner_id):
                perms_message += "my Owner!"
            else:
                if ctx.guild.get_member(user.id) is None:
                    try:
                        await ctx.guild.fetch_ban(user)
                    except discord.NotFound:
                        perms_message += "not a member of this server"
                    else:
                        perms_message += "banned from this server"
                elif user.guild_permissions.administrator:
                    perms_message += "a server administrator"
                else:
                    perms_message = f"{user.name}#{user.discriminator} is a standard user on this server"
                if user.bot:
                    perms_message += " (and a bot)"
                perms_message += "."

        perms_message = ctx.author.mention + ", " + perms_message

        await ctx.send(perms_message)

    @commands.command(name="ping")
    async def ping(self, ctx):
        """
        Usage:
            {command_prefix}ping

        Test the operation of the bot & its ping
        """
        before = time.monotonic()
        ping_msg = await ctx.send("Pong!")
        after = time.monotonic()
        ping = (after - before) * 1000
        await ping_msg.edit(content=f"Pong! (took {ping:.0f}ms)")

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """
        Usage:
            {command_prefix}uptime

        Gives the bot's uptime
        """
        seconds = time.time() - self.bot.start_time
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        await ctx.send(
            f"I've been online for `{int(w)}w : {int(d)}d : {int(h)}d : {int(h)}h : {int(m)}m : {int(s)}s"
        )

    @commands.command(aliases=["user", "userinfo"])
    async def playerinfo(self, ctx, user: discord.Member = None):
        """
        Usage:
            {command_prefix}user, {command_prefix}userinfo

        Gives info about a particular user. If a user isn't passed then the shown info is yours.
        """
        if not user:
            user = ctx.author

        roles = [role.name.replace("@", "@\u200b") for role in user.roles]
        msg = [
            ("Name", user.name),
            ("Discrim", user.discriminator),
            ("Display Name", user.display_name),
            ("Joined at", user.joined_at),
            ("Created at", user.created_at),
            ("Server Roles", ", ".join(roles)),
            ("Status", user.status),
        ]
        await ctx.send(misc.neatly(msg))

    @commands.command(aliases=["server", "serverinfo"])
    async def serverinfo(self, ctx):
        """
        Usage:
            {command_prefix}server, {command_prefix}serverinfo

        Gives info about the current server.
        """
        server = ctx.guild

        msg = [
            ("Name", server.name),
            ("ID", server.id),
            ("Region", server.region),
            ("Owner", server.owner),
            ("Member Count", len(server.members)),
            ("Role Count", len(server.roles)),
            ("Icon", server.icon_url),
        ]

        await ctx.send(misc.neatly(msg))


class Choices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="choose")
    async def choose(self, ctx, *, text: str):
        """
        Chooses between one or more options, each separated by "or."
        Can be optonally begun with numbers separated by forward slashes (i.e., 50/50), which weight different options -- if this is left out, each option will be given equal weight
        """
        textlist = text.split()
        if "/" in textlist[0]:
            weights = [int(x) for x in textlist[0].split("/")]
            text = " ".join(textlist[1:])
            choices = text.split(" or ")
            choice_len = len(choices)
            weight_len = len(weights)
            if choice_len < weight_len:
                weights = weights[:choice_len]
            elif choice_len > weight_len:
                weight_co = sum(weights)
                rem_dist = choice_len - weight_len
                weight_div = (100 - weight_co) // rem_dist
                weights.extend([weight_div] * rem_dist)
            the_choice = random.choices(choices, weights, k=1)
        else:
            choices = text.split(" or ")
            the_choice = random.choices(choices, k=1)
        statement_options = [
            f"I pick **{the_choice}**!",
            f"No need to discuss, it's **{the_choice}**.",
            f"Why even ask? **{the_choice}**, obviously.",
            f"I mean, if you had a brain, you'd already know it's **{the_choice}**.",
            f"**{the_choice}**, of course.",
            f"It's {the_choice}, which you'd have known if you were actually good at this.",
            f"The answer is {the_choice}!",
        ]
        pick = random.choice(statement_options)
        await ctx.send(pick)


def setup(bot):
    bot.add_cog(Information(bot))
    bot.add_cog(Choices(bot))
