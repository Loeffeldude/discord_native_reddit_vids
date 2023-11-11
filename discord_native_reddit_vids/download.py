import yt_dlp
import pathlib
import uuid

# discord has a 8MB limit on file uploads
MAX_VIDEO_SIZE = 8 * 1024 * 1024  # 8MB
MAX_DURATION = 60 * 5  # 5 minutes


def download_video(reddit_url: str) -> pathlib.Path | None:
    """Downloads a video from a reddit post"""
    video_id = uuid.uuid4()
    out_path = pathlib.Path("tmp", f"{video_id}.mp4")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_path.as_posix(),
        "merge_output_format": "mp4",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(reddit_url, download=False)

            # Check if the video is too big
            if info["duration"] > MAX_DURATION:
                return None

            ydl.download([reddit_url])
        except yt_dlp.utils.DownloadError as download_error:
            # This is awful but I don't know how else to do it
            # I guess its pythonic lol
            if download_error.msg.lower() in "no media found":
                return None
            else:
                raise download_error

    # check if the video is too big
    if out_path.stat().st_size > MAX_VIDEO_SIZE:
        out_path.unlink()
        return None

    return out_path


def download_videos(reddit_urls: list[str]) -> list[pathlib.Path]:
    """Downloads videos from a list of reddit urls"""
    video_paths = []
    for url in reddit_urls:
        video_paths.append(download_video(url))
    return [path for path in video_paths if path is not None]
