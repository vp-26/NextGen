import sys
import os
from yt_dlp import YoutubeDL


def fetch_media_data(url):
    # Ab cookies.txt aur fetch.py dono same api folder mein hain, toh path bilkul direct hoga
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_path = os.path.join(current_dir, "cookies.txt")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "best",
        # Agar api folder ke andar cookies.txt milegi toh use karega, nahi toh None
        "cookiefile": cookies_path if os.path.exists(cookies_path) else None,
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

            # 1. Multiple entries / Carousel posts ke liye
            if "entries" in info:
                media_list = []
                for entry in info["entries"]:
                    if not entry:
                        continue
                    if "url" in entry:
                        media_list.append(entry["url"])
                    elif "formats" in entry and len(entry["formats"]) > 0:
                        media_list.append(entry["formats"][-1]["url"])

                if media_list:
                    return {
                        "status": "success",
                        "url": media_list[0],
                        "type": "multiple",
                    }

            # 2. Single Video/Image/Audio ke liye
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

                return {"status": "success", "url": media_url, "type": media_type}
            else:
                return {
                    "status": "error",
                    "message": "Could not find any downloadable content.",
                }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Local testing ke liye
if __name__ == "__main__":
    import json

    if len(sys.argv) > 1:
        input_url = sys.argv[1]
        print(json.dumps(fetch_media_data(input_url)))
    else:
        print(json.dumps({"status": "error", "message": "No URL provided."}))
