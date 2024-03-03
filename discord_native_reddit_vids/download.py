from typing import Iterable, Callable
import uuid
import discord
import dataclasses
import re
import yt_dlp
import discord_native_reddit_vids.settings as settings
import asyncio
from hurry.filesize import size
import logging
import shutil

logger = logging.getLogger(__name__)


class DownloadHandler:

    url_regexes: Iterable[re.Pattern[str]]
    verbose_name: str
    name: str

    @property
    def _YTD_DEFAULT_OPTS(self):
        return {
            "format": f"(bestvideo+bestaudio)[filesize<{size(settings.MAX_UPLOAD_VIDEO_SIZE)}B]/bestvideo+bestaudio",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
        }

    def _extract_urls(self, pattern, message_str: str):
        return [match.group(0) for match in re.finditer(pattern, message_str)]

    def extract_urls(self, message_str: str):
        return list(
            set(
                [
                    url
                    for re_pattern in self.url_regexes
                    for url in self._extract_urls(re_pattern, message_str)
                ]
            )
        )

    async def handle(self, message: discord.Message):
        urls = self.extract_urls(message.content)

        if not urls:
            return

        await asyncio.gather(*[self.download_handler(url, message) for url in urls])

    def progress_bar(self, progress: float, length: int = 20):
        return f"[{'#' * int(progress * length)}{'-' * int((1 - progress) * length)}]"

    async def download_handler(self, url: str, message: discord.Message):
        try:
            id = str(uuid.uuid4()).replace("-", "")
            tmp_path = settings.BASE_DIR / f"tmp/{self.name}/{id}.mp4"

            embed_message: None | discord.Message = None
            progress = 0

            # here we create our embed that tracks the download progress
            def get_embed(info: dict, progress: float = 0):
                embed = discord.Embed(
                    title=f"Downloading {info['title']} using {self.verbose_name}",
                    description=f"Progress\n{self.progress_bar(progress)}",
                    color=discord.Color.blue(),
                )

                embed.set_thumbnail(
                    url="https://media.tenor.com/qYSjiwLs2zgAAAAj/fries-spin.gif"
                )  # url=f"{settings.HOST_URL}/loading.gif")

                return embed

            def progress_hook(info):

                if info["status"] != "downloading":
                    return

                if not embed_message:
                    return
                nonlocal progress
                if "total_bytes" not in info:
                    return
                if "downloaded_bytes" not in info:
                    return

                progress = info["downloaded_bytes"] / info["total_bytes"]

            ydl_opts = {
                "outtmpl": tmp_path.as_posix(),
                **self._YTD_DEFAULT_OPTS,
                "progress_hooks": [progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await self.get_info(url, ydl)

                if info is None:
                    return

                if not self.should_download(info):
                    return

                embed_message = await message.reply(
                    embed=get_embed(info, progress), mention_author=False
                )

                download_task = asyncio.create_task(self.download(url, ydl))

                # while not download_task.done():
                #     if progress != 0:
                #         await embed_message.edit(embed=get_embed(info, progress))

                #     await asyncio.wait([download_task, asyncio.sleep(0.05)])

                await download_task

            should_host = tmp_path.stat().st_size > settings.MAX_UPLOAD_VIDEO_SIZE

            send_embed = discord.Embed(
                title=f"{info['title']} posted by {message.author.display_name}",
                color=discord.Color.green(),
            )

            if should_host:
                (settings.BASE_DIR / f"public/videos/{self.name}/").mkdir(exist_ok=True)

                # copy isntead of move because this dir is mounted (invalid cross-device link)
                target_path = (
                    settings.BASE_DIR / f"public/videos/{self.name}/{tmp_path.name}"
                )

                # copy the file to the public folder
                shutil.copy(str(tmp_path), str(target_path))

                await embed_message.edit(
                    content=settings.HOST_URL
                    + f"/videos/{self.name}/{target_path.name}",
                    embed=send_embed,
                )

            else:
                await embed_message.edit(
                    attachments=[discord.File(tmp_path)],
                    embed=send_embed,
                )
                tmp_path.unlink()
        except Exception as e:
            if embed_message:
                await embed_message.edit(
                    embed=discord.Embed(
                        title="An error occurred",
                        description=f"An error occurred while processing the video\n{e}",
                        color=discord.Color.red(),
                    )
                )
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def should_download(self, info: dict):
        return info.get("duration", 0) < settings.MAX_DURATION

    async def get_info(self, url: str, ydl: yt_dlp.YoutubeDL) -> dict | None:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, ydl.extract_info, url, False)
        except yt_dlp.utils.DownloadError as download_error:
            if "no media found" in download_error.msg.lower():
                return None

            raise download_error

    async def download(self, url: str, ydl: yt_dlp.YoutubeDL):
        loop = asyncio.get_event_loop()

        logger.info(f"Downloading {url}")

        await loop.run_in_executor(None, ydl.download, [url])


class RedditDownloadHandler(DownloadHandler):
    verbose_name = "Reddit Downloader"
    name = "reddit"
    url_regexes = [
        re.compile(
            r"(https?\:\/\/((old\.|www\.)?reddit\.com\/r\/[\w]+\/[\w]*\/[\w]+\/\S*))",
        ),
        re.compile(r"https?\:\/\/v\.redd\.it\/[\w]+"),
        re.compile(r"https?\:\/\/www\.reddit\.com\/r\/[\w]+/s/[\w]+"),
    ]


class TwitterDownloadHandler(DownloadHandler):
    verbose_name = "Twitter Downloader"
    name = "twitter"
    url_regexes = [
        re.compile(r"https?\:\/\/twitter\.com\/[\w]+/status/[\w]+"),
    ]


class YT18PlusDownloadHandler(DownloadHandler):

    url_regexes = [
        re.compile(r"https?\:\/\/www\.youtube\.com\/watch\?v=[\w]+"),
        re.compile(r"https?\:\/\/youtu\.be/[\w]+"),
    ]
    verbose_name = "Youtube Downloader"
    name = "youtube"

    def should_download(self, info: dict):
        is_over_age_limit = info.get("age_limit", 0) >= 18
        print(is_over_age_limit)
        return super().should_download(info) and is_over_age_limit
