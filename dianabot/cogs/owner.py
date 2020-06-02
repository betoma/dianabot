import discord
from discord.ext import commands

import logging
log = logging.getLogger('discord')

class Ownership(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shutdown",hidden=True)
    @commands.is_owner()
    async def shutdown(self):
        await self.bot.logout()
    
    @shutdown.error
    async def shutdown_error(self,ctx,error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("Sorry, this command is for Sparky only!")

    @commands.command(name="status",hidden=True)
    @commands.is_owner()
    async def change_status(self,status:str,*,text:str):
        new_activity = discord.Game(text)
        if status == "online":
            new_status = discord.Status.online
        elif status == "offline":
            new_status = discord.Status.offline
        elif status == "afk":
            new_status = discord.Status.idle
        elif status == "dnd":
            new_status = discord.Status.dnd
        await self.bot.change_presence(activity=new_activity, status=new_status)
    
    @change_status.error
    async def change_status_error(self,ctx,error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("Sorry, this command is for Sparky only!")

def setup(bot):
    bot.add_cog(Ownership(bot))