import os
import logging

from dianabot import DianaBot


def init_logging():
    logger = logging.getLogger("discord")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
    handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    )
    logger.addHandler(handler)


if __name__ == "__main__":
    init_logging()

    log = logging.getLogger(__name__)

    token = os.environ.get("DISCORD_TOKEN")

    if token is None:
        log.error("DISCORD_TOKEN env variable not set. Set it before running the bot.")
        exit(-1)

    log.info("Starting Diana Bot.")

    try:
        dianabot = DianaBot()
        dianabot.run(token)
    except:  # pylint: disable=bare-except
        log.error("Something went wrong during execution. Exiting...", exc_info=1)

