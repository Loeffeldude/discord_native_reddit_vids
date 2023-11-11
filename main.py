import discord
import dotenv
import os
import discord_native_reddit_vids.reddit as reddit
import discord_native_reddit_vids.download as download
import logging

logger = logging.getLogger("discord_native_reddit_vids")
logger.setLevel(logging.DEBUG)
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(
    intents=intents,
)


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    urls = reddit.get_reddit_urls(message.content)

    if len(urls) == 0:
        return
    
    urls_str = "\n".join(urls)
    logger.debug(f"URLS: {urls_str}")

    logger.info(f"Downloading {len(urls)} videos from {message.author.name}")

    video_paths = download.download_videos(urls)

    for video_path in video_paths:
        try:
            await message.channel.send(file=discord.File(video_path))
        finally:
            video_path.unlink()

if __name__ == "__main__":
    client.run(os.getenv("DISCORD_TOKEN"))
