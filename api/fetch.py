import sys
import json
from yt_dlp import YoutubeDL


def get_media_download_url(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "best",
        "cookiefile": "cookies.txt",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        "extractor_args": {
            "instagram": {
                "max_comments": 0,
            }
        },
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "entries" in info:
                media_list = []
                for entry in info["entries"]:
                    if "url" in entry:
                        media_list.append(entry["url"])
                    elif "formats" in entry and len(entry["formats"]) > 0:
                        media_list.append(entry["formats"][-1]["url"])

                if media_list:
                    return json.dumps(
                        {"status": "success", "url": media_list[0], "type": "multiple"}
                    )

            media_url = None
            media_type = "video"

            if "url" in info:
                media_url = info["url"]
            elif "formats" in info and len(info["formats"]) > 0:
                media_url = info["formats"][-1]["url"]

            if media_url:
                if "ext" in info:
                    if info["ext"] in ["mp3", "m4a", "wav", "aac"]:
                        media_type = "audio"
                    elif info["ext"] in ["jpg", "jpeg", "png", "webp"]:
                        media_type = "image"

                if "audio" in media_url or (
                    "vcodec" in info and info["vcodec"] == "none"
                ):
                    media_type = "audio"

                return json.dumps(
                    {"status": "success", "url": media_url, "type": media_type}
                )
            else:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Could not find any downloadable content.",
                    }
                )

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_url = sys.argv[1]
        print(get_media_download_url(input_url))
    else:
        print(json.dumps({"status": "error", "message": "No URL provided."}))
