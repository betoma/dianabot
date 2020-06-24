import discord
from discord.ext import commands


def neatly(entries, colors=""):
    """
    Neatly order text
    """
    width = max(map(lambda t: len(t[0]), entries))
    output = [f"```{colors}"]
    for name, entry in entries:
        output.append("\u200b{0:>{width}}: {1}".format(name, entry, width=width))
    output.append("```")
    return "\n".join(output)


def get_prefix(bot, msg):
    if msg.guild.id in bot.config.prefixes:
        prefixes = bot.config.prefixes[msg.guild.id]
    else:
        prefixes = ["&"]
    return commands.when_mentioned_or(*prefixes)(bot, msg)


def is_author(user, msg):
    return user == msg.author


def message_embed(msg):
    permalink = f"[→ Go to message]({msg.jump_url})\n"
    embed = discord.Embed(
        description=permalink + msg.content,
        color=msg.author.color,
        timestamp=msg.created_at,
    ).set_author(
        name=msg.author.display_name, icon_url=msg.author.avatar_url_as(format="png")
    )
    attachments_are_listed = False
    attachment_list = []
    embed_image_unset = True
    number_rich_embed = 0

    def is_image_url(url):
        return url.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))

    if msg.attachments:
        attachments_are_listed = len(msg.attachments) > 1 or not is_image_url(
            msg.attachments[0].url
        )
        for message_attach in msg.attachments:
            if is_image_url(message_attach.url) and embed_image_unset:
                embed.set_image(url=message_attach.url)
                embed_image_unset = False
            attachment_list.append(f"[{message_attach.filename}]({message_attach.url})")
    if msg.embeds:
        for msg_embed in msg.embeds:
            if msg_embed.type == "rich":
                number_rich_embed += 1
            elif msg_embed.type == "image":
                if (
                    embed_image_unset
                    and msg_embed.thumbnail.url is not discord.Embed.Empty
                ):
                    embed.set_image(url=msg_embed.thumbnail.url)
                    embed_image_unset = False

    if attachments_are_listed:
        embed.add_field(name="📎", value="\n".join(attachment_list), inline=False)

    if number_rich_embed == 1:
        embed.set_footer(text="📄 Message has a rich embed")
    elif number_rich_embed > 1:
        embed.set_footer(text=f"📄 Message has {number_rich_embed} rich embeds")

    return embed
