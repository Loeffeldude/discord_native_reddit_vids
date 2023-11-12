import discord
import dotenv
import os
import discord_native_reddit_vids.reddit as reddit
import discord_native_reddit_vids.download as download
import logging

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]%(name)s: %(message)s",
)

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

    # limit the number of url to 5
    urls = urls[:5]

    logger.info(f"Downloading {len(urls)} videos from {message.author.name}")

    video_download_results = download.download_videos(urls)

    logger.info(
        f"Sending {len([res.success for res in video_download_results])} videos to {message.author.name}"
    )

    for download_result in video_download_results:
        if download_result.success is False:
            logger.info(f"Failed to download {download_result.url}")
            logger.info(f"Reason: {download_result.reason}")
            await message.reply(
                f"Failed to download: {download_result.reason}", mention_author=False
            )
            continue
        try:
            logger.info(f"Sending {download_result.url}")
            await message.reply(
                content=download_result.url,
                file=discord.File(download_result.path),
                mention_author=False,
                suppress_embeds=True,
            )
        finally:
            download_result.path.unlink()


if __name__ == "__main__":
    logger.info("Starting discord_native_reddit_vids")
    client.run(os.getenv("DISCORD_TOKEN"), log_handler=None)
