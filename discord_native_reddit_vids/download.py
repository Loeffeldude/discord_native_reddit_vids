from typing import Optional
import yt_dlp
import pathlib
import uuid
import logging
import dataclasses
import enum

logger = logging.getLogger("bot")

MAX_VIDEO_SIZE = 300 * 1024 * 1024  # 300MB
MAX_DURATION = 60 * 10  # 10 minutes


class DownloadErrorReason(enum.Enum):
    NO_MEDIA = "no media found"
    TOO_LONG = "too long"
    TOO_LARGE = "too large"

    def __str__(self):
        if self == DownloadErrorReason.NO_MEDIA:
            return "The reddit post does not have any video media"
        elif self == DownloadErrorReason.TOO_LONG:
            return "The reddit video is too long"
        elif self == DownloadErrorReason.TOO_LARGE:
            return "The reddit video's filesize is too large"
        else:
            return "Unknown error"


@dataclasses.dataclass
class SucessDownloadResult:
    path: pathlib.Path
    url: str

    @property
    def success(self) -> bool:
        return True

    def should_host(self):
        """Returns true if we host the video our selfs for example if the video is too large for discord"""
        DISCORD_UPLOAD_LIMIT = 8 * 1024 * 1024  # 8MB
        
        return self.path.stat().st_size > DISCORD_UPLOAD_LIMIT


@dataclasses.dataclass
class FailureDownloadResult:
    reason: DownloadErrorReason
    url: str

    @property
    def success(self) -> bool:
        return False


def download_video(
    reddit_url: str, max_duration: Optional[float] = None, max_size: Optional[int] = None
) -> SucessDownloadResult | FailureDownloadResult:
    """Downloads a video from a reddit post"""
    video_id = uuid.uuid4()
    out_path = pathlib.Path("tmp", f"{video_id}.mp4")

    max_duration = max_duration or MAX_DURATION
    max_size = max_size or MAX_VIDEO_SIZE

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_path.as_posix(),
        "merge_output_format": "mp4",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(reddit_url, download=False)

            if info["duration"] > max_duration:
                return FailureDownloadResult(
                    reason=DownloadErrorReason.TOO_LONG, url=reddit_url
                )

            ydl.download([reddit_url])
        except yt_dlp.utils.DownloadError as download_error:
            # This is awful but I don't know how else to do it
            # I guess its pythonic lol
            if download_error.msg.lower() in "no media found":
                return FailureDownloadResult(
                    url=reddit_url, reason=DownloadErrorReason.NO_MEDIA
                )
            else:
                raise download_error

    is_too_large = out_path.stat().st_size > max_size

    if is_too_large:
        out_path.unlink()
        return FailureDownloadResult(
            reason=DownloadErrorReason.TOO_LARGE, url=reddit_url
        )

    return SucessDownloadResult(path=out_path, url=reddit_url)


def download_videos(
    reddit_urls: list[str],
) -> list[SucessDownloadResult | FailureDownloadResult]:
    """Downloads videos from a list of reddit urls"""
    video_paths = []
    for url in reddit_urls:
        video_paths.append(download_video(url))
    return [path for path in video_paths]
