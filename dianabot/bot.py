import time
import discord
from discord.ext import commands

from dianabot.config import Config
from dianabot.utils.misc import get_prefix

start = time.time()


class DianaBot(commands.Bot):
    def __init__(
        self,
        description="Hello! I'm Diana, a bot made by Sparksbet to provide some utilities.",
    ):

        self.version = "0.1"

        print("-----------------------------\n")
        print("Loading Configuration...\n")

        self.config = Config()

        super().__init__(
            command_prefix=get_prefix,
            description=description,
            owner_id=self.config.owner_id,
            fetch_offline_members=True,
        )
        self.config.start_up(self)

        print(f"Currently Running DianaBot v{self.version}")

        self.start_time = start

    async def on_ready(self):
        print("\n\nConnected!\n")

        await self.config.establish_connection()

        print("Database Connected!\n")

        if len(self.guilds) == 0:
            app_info = await self.application_info()
            join_url = discord.utils.oauth_url(app_info.id) + "&permissions=66321471"
            print(
                "{bot_name} is not in any servers!\nYou can add {bot_name} to a server at:\n{url}".format(
                    bot_name=self.config.bot_name, url=join_url
                )
            )
        elif len(self.guilds) < 16:
            print("Current Servers:")
            for server in self.guilds:
                print(f" - {server.name} ({server.id})")
            print()
        else:
            print("Currently on {} servers\n".format(len(self.guilds)))

        default_activity = discord.Game("&help, /ðæŋks/")
        await self.change_presence(
            activity=default_activity, status=discord.Status.online
        )

    async def on_server_join(self, server):
        if self.config.debug:
            print(f"[SERVER] Joined {server.name} (Owner: {server.owner.name})")

        await self.config.add_server(server.id)

    async def on_server_remove(self, server):
        if self.config.debug:
            print(f"[SERVER] Left {server.name} (Owner: {server.owner.name})")

    @bot.listen()
    async def on_message(self, message):
        await self.process_commands(message)


if __name__ == "__main__":
    bot = DianaBot()
    bot.run()
