from collections import defaultdict
import os

import aiomysql
import pymysql


class Config:
    def __init__(self, debug: bool = False):
        self.bot = None
        self.pool = None
        self.db_kwargs = {
            "host": os.environ.get("SQL_HOST"),
            "port": os.environ.get("SQL_PORT"),
            "user": os.environ.get("SQL_USER"),
            "password": os.environ.get("SQL_PASS"),
            "db": os.environ.get("SQL_DB"),
            "charset": "utf8mb4",
        }
        self.bot_name = "Diana"
        self.owner_id = os.environ.get("OWNER_ID")
        self.debug = debug
        self.prefixes = defaultdict(list)
        self.pastebin_dev_key = {}
        self.greylist = defaultdict(lambda: defaultdict(dict))
        self.mod_notif_channel = {}
        self.mod_role = {}
        self.laogai_id = {}
        self.laogai_lite_id = {}
        self.wanshitong = defaultdict(lambda: defaultdict(list))

        self.VAR_TAB = {
            "ModRole": self.mod_role,
            "ModNotifChannel": self.mod_notif_channel,
            "PastebinKey": self.pastebin_dev_key,
            "LaogaiRole": self.laogai_id,
            "LaogaiLiteRole": self.laogai_lite_id,
        }

    def start_up(self, bot):
        self.bot = bot

        connection = pymysql.connect(
            cursorclass=pymysql.cursors.DictCursor, **self.db_kwargs
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS `Servers` (`ServerId` TEXT NOT NULL, `ModRole` TEXT, `ModNotifChannel` TEXT, `PastebinKey` TEXT, `LaogaiRole` TEXT, `LaogaiLiteRole` TEXT, PRIMARY KEY (`ServerId`))"
                )
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS `Prefixes` (`ServerId` TEXT NOT NULL, `Prefix` TEXT NOT NULL, PRIMARY KEY (`ServerId`, `Prefix`), FOREIGN KEY (`ServerId`) REFERENCES `Servers`(`ServerId`))"
                )
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS `Greylist` (`ServerId` TEXT NOT NULL, `Word` TEXT NOT NULL, `Channel` TEXT NOT NULL, `Ping` BOOL, PRIMARY KEY (`ServerId`, `Channel`), FOREIGN KEY (`ServerId`) REFERENCES `Servers`(`ServerId`))"
                )
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS `Wanshitong` (`IncidentId` BIGINT NOT NULL AUTO_INCREMENT, `ServerId` TEXT NOT NULL, `User` TEXT NOT NULL, `Date` DATETIME NOT NULL, `Description` TEXT NOT NULL, `ReportingMod` TEXT NOT NULL, PRIMARY KEY (`IncidentId`), FOREIGN KEY (`ServerId`) REFERENCES `Servers`(`ServerId`))"
                )

                cursor.execute("SELECT `ServerId` FROM `Servers`")
                db_servers = [row["ServerId"] for row in cursor.fetchall()]
                for guild in self.bot.guilds:
                    if guild not in db_servers:
                        cursor.execute(
                            f"INSERT INTO `Servers` (`ServerId`) VALUES ({guild.id})"
                        )
                        cursor.execute(
                            f"INSERT INTO `Prefixes` (`ServerId`, `Prefix`) VALUES ({guild.id}, '&')"
                        )

            connection.commit()

            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM `Prefixes`")
                for row in cursor.fetchall():
                    self.prefixes[row["ServerId"]].append(row["Prefix"])
                cursor.execute("SELECT * FROM `Servers`")
                for row in cursor.fetchall():
                    self.pastebin_dev_key[row["ServerId"]] = row["PastebinKey"]
                    self.mod_role[row["ServerId"]] = row["ModRole"]
                    self.mod_notif_channel[row["ServerId"]] = row["ModNotifChannel"]
                    self.laogai_id[row["ServerId"]] = row["LaogaiRole"]
                    self.laogai_lite_id[row["ServerId"]] = row["LaogaiLiteRole"]
                cursor.execute("SELECT * FROM `Greylist`")
                for row in cursor.fetchall():
                    self.greylist[row["ServerId"]][row["Channel"]][row["Word"]] = row[
                        "Ping"
                    ]
                cursor.execute("SELECT * from `Wanshitong`")
                for row in cursor.fetchall():
                    self.wanshitong[row["ServerId"]][row["User"]].append(
                        {
                            "date": row["Date"],
                            "description": row["Description"],
                            "reporting mod": row["ReportingMod"],
                        }
                    )

        finally:
            connection.close()

    async def establish_connection(self):
        self.pool = await aiomysql.create_pool(minsize=0, maxsize=10, **self.db_kwargs)

    async def add_server(self, server_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"SELECT EXISTS(SELECT 1 FROM `Servers` WHERE `ServerId` = '{server_id}' LIMIT 1)"
                )
                if not await cursor.fetchone():
                    await cursor.execute(
                        f"INSERT INTO `Servers` (`ServerId`) VALUES ('{server_id}')"
                    )
                    await conn.commit()

    async def close_connection(self):
        self.pool.close()
        await self.pool.wait_closed()

    async def add_value(
        self,
        server_id,
        table,
        value,
        variable: str = None,
        channel: str = None,
        pingable: bool = None,
        user: str = None,
        date=None,
        desc: str = None,
        mod: str = None,
    ):
        if table == "Servers":
            if variable not in self.VAR_TAB:
                raise ValueError
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        f"UPDATE `{table}` SET `{variable}`='{value}' WHERE `ServerId` = '{server_id}'"
                    )
                    await conn.commit()
            self.VAR_TAB[variable] = value
        elif table in {"Prefixes", "Greylist", "Wanshitong"}:
            if table == "Prefixes":
                self.prefixes[server_id].append(value)
                variables = "`ServerId`, `Prefix`"
                values = f"'{server_id}', '{value}'"
            elif table == "Greylist":
                self.greylist[server_id][channel][value] = pingable
                variables = "`ServerId`,`Word`,`Channel`,`Ping`"
                values = f"'{server_id}', '{value}', '{channel}', '{pingable}'"
            elif table == "Wanshitong":
                self.wanshitong[server_id][user].append(
                    {
                        "date": date,
                        "description": desc,
                        "reporting mod": mod,
                    }
                )
                variables = "`ServerId`, `User`, `Date`, `Description`, `ReportingMod`"
                values = f"'{server_id}', '{user}','{date}', '{desc}', '{mod}'"
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        f"INSERT INTO `{table}` ({variables}) VALUES ({values})"
                    )
                    await conn.commit()
        else:
            raise ValueError("You must select a valid table name.")

    async def remove_value(
        self,
        server_id: str,
        table: str,
        variable: str,
        value: str = None,
        spec_var: str = None,
        spec_val: str = None,
    ):
        if table == "Servers":
            if variable not in self.VAR_TAB:
                raise ValueError("Invalid variable choice.")
            if variable == "ServerId":
                raise ValueError("Cannot remove ServerId variable.")
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        f"UPDATE `{table}` SET `{variable}`= NULL WHERE `ServerId` = '{server_id}'"
                    )
                    await conn.commit()
        elif table in {"Prefixes", "Greylist", "Wanshitong"}:
            send = f"DELETE FROM `{table}` WHERE `ServerId` = '{server_id}' AND `{variable}` = {value}"
            if spec_var and spec_val:
                send += f" AND `{spec_var}` = {spec_val}"
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(send)
                    await conn.commit()
        else:
            raise ValueError("You must select a valid table name.")

    async def wipe_server(self, server_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for table in {"Servers", "Prefixes", "Greylist", "Wanshitong"}:
                    await cursor.execute(
                        f"DELETE FROM `{table}` WHERE `ServerId` = '{server_id}'"
                    )
                await conn.commit()