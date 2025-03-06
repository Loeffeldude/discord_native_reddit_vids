import asyncio
import re
from typing import Optional
import discord
import dotenv
import os
import discord_native_reddit_vids.download as download
import logging
import discord_native_reddit_vids.settings as settings


logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(
    intents=intents,
)


handler: list[download.DownloadHandler] = [
    download.RedditDownloadHandler(),
    download.TwitterDownloadHandler(),
    download.YT18PlusDownloadHandler(),
    download.InstagramDownloadHandler(),
]


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    print(f"Message from {message.author}: {message.content}")

    await asyncio.gather(*[h.handle(message) for h in handler])


if __name__ == "__main__":
    dotenv.load_dotenv()

    logger.info("Starting discord_native_reddit_vids")
    client.run(settings.DISCORD_TOKEN, log_handler=None)
