import sys
import os
import json
from yt_dlp import YoutubeDL

IMAGE_EXT = ("jpg", "jpeg", "png", "webp")
AUDIO_EXT = ("mp3", "m4a", "wav", "aac")


def has_audio(f):
    return f.get("acodec") != "none"


def has_video(f):
    return f.get("vcodec") != "none"


def pick_url(info):
    """Hamesha aisa URL chuno jisme awaaz ho. Video-only stream kabhi nahi."""
    formats = [f for f in (info.get("formats") or []) if f.get("url")]

    # 1. Video + audio dono wale formats (sabse best last mein hota hai)
    both = [f for f in formats if has_video(f) and has_audio(f)]
    if both:
        return both[-1]["url"]

    # 2. Yt-dlp ne jo single format chuna wo (image/audio posts ke liye)
    if info.get("url"):
        return info["url"]

    # 3. Aakhri fallback
    if formats:
        return formats[-1]["url"]
    return None


def detect_type(info):
    ext = (info.get("ext") or "").lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in AUDIO_EXT or info.get("vcodec") == "none":
        return "audio"
    return "video"


def fetch_media_data(url):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_path = os.path.join(current_dir, "cookies.txt")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        # Pehle video+audio single file, phir koi bhi audio wali, phir best
        "format": "b[vcodec!=none][acodec!=none]/b[acodec!=none]/b",
        "cookiefile": cookies_path if os.path.exists(cookies_path) else None,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        "extractor_args": {"instagram": {"max_comments": 0}},
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Carousel / playlist
            if info.get("entries"):
                urls = []
                for entry in info["entries"]:
                    if not entry:
                        continue
                    u = pick_url(entry)
                    if u:
                        urls.append(u)
                if urls:
                    return {
                        "status": "success",
                        "url": urls[0],
                        "urls": urls,
                        "type": "multiple",
                    }

            media_url = pick_url(info)
            if not media_url:
                return {
                    "status": "error",
                    "message": "Could not find any downloadable content.",
                }

            return {"status": "success", "url": media_url, "type": detect_type(info)}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(fetch_media_data(sys.argv[1])))
    else:
        print(json.dumps({"status": "error", "message": "No URL provided."}))