from typing import Optional
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

    reply_message: Optional[discord.Message] = await message.reply(
        "Downloading videos...", mention_author=False
    )

    video_download_results = download.download_videos(urls)

    logger.info(
        f"Sending {len([res.success for res in video_download_results])} videos to {message.author.name}"
    )

    try:
        for download_result in video_download_results:
            if isinstance(download_result, download.FailureDownloadResult):
                logger.info(f"Failed to download {download_result.url}")
                logger.info(f"Reason: {download_result.reason}")

                if download_result.reason == download.DownloadErrorReason.NO_MEDIA:
                    continue

                if reply_message:
                    await reply_message.delete()
                    reply_message = None

                await reply_message.edit(
                    content=f"Failed to download: {download_result.reason}"
                )
            else:
                if reply_message:
                    await reply_message.delete()
                    reply_message = None

                if download_result.should_host():
                    base_dir = download_result.path.parent.parent
                    move_to = base_dir / "videos" / download_result.path.name
                    download_result.path.rename(move_to)

                    url = f"{os.getenv('HOST_URL')}/videos/{download_result.path.name}"

                    await message.reply(content=url, mention_author=False)
                else:
                    logger.info(f"Sending {download_result.url}")
                    await message.reply(
                        content=download_result.url,
                        file=discord.File(download_result.path),
                        mention_author=False,
                        suppress_embeds=True,
                    )

    finally:
        for download_result in video_download_results:
            if isinstance(download_result, download.SucessDownloadResult):
                if download_result.path.exists():
                    download_result.path.unlink()


if __name__ == "__main__":
    logger.info("Starting discord_native_reddit_vids")
    client.run(os.getenv("DISCORD_TOKEN"), log_handler=None)
