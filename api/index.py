from flask import Flask, request, jsonify, redirect, render_template, g, Response
from pymongo import MongoClient
from datetime import datetime
from urllib.parse import urlparse
import requests
import uuid
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, "templates")

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24).hex()

# MONGO_URI ab environment variable se aayega (Vercel/Render settings mein daalo)
MONGO_URI = os.environ["MONGO_URI"]

client = MongoClient(MONGO_URI)
db = client["VeloraDrive"]
stats_collection = db["website_stats"]
qr_collection = db["qr_links"]
url_log = db["url_log"]

try:
    client.admin.command("ping")
    print("MongoDB Connected Successfully")
    stats_collection.update_one(
        {"name": "main"},
        {"$setOnInsert": {"visitors": 0, "downloads": 0}},
        upsert=True,
    )
    # QR links 1 ghante baad auto-delete
    qr_collection.create_index("created_at", expireAfterSeconds=3600)
except Exception as e:
    print("MongoDB Connection Error:", e)

ALLOWED_DOMAINS = (
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "fb.watch",
)

# Thumbnail sirf in image servers se laya jayega
THUMB_HOSTS = (
    "cdninstagram.com",
    "fbcdn.net",
    "ytimg.com",
    "ggpht.com",
    "googleusercontent.com",
)


def host_matches(u, domains):
    p = urlparse(u)
    host = (p.hostname or "").lower()
    return p.scheme in ("http", "https") and any(
        host == d or host.endswith("." + d) for d in domains
    )


def get_stats():
    stats = stats_collection.find_one({"name": "main"})
    if not stats:
        stats = {"name": "main", "visitors": 0, "downloads": 0}
        stats_collection.insert_one(stats)
    return stats


# Visitor Counter
@app.before_request
def visitor_counter():
    if request.path in [
        "/ping",
        "/ajax_url",
        "/track_download",
        "/thumb",
        "/favicon.ico",
    ] or request.path.startswith("/static"):
        return

    if request.cookies.get("visitor_counted") == "yes":
        return

    try:
        stats_collection.update_one({"name": "main"}, {"$inc": {"visitors": 1}})
        g.set_visitor_cookie = True
    except Exception as e:
        print("Error updating visitor count in DB:", e)


@app.after_request
def after_request(response):
    if getattr(g, "set_visitor_cookie", False):
        response.set_cookie(
            "visitor_counted",
            "yes",
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="Lax",
            secure=request.is_secure,
        )
    return response


# Ping route (uptime monitoring)
@app.route("/ping")
def ping():
    return jsonify({"status": "alive", "message": "Keep awake request successful!"}), 200


# Home
@app.route("/")
def index():
    try:
        stats = get_stats()
        return render_template(
            "index.html",
            total_visitors=stats["visitors"],
            total_downloads=stats["downloads"],
        )
    except Exception as e:
        print("Index error:", e)
        return "Something went wrong", 500


# Contact
@app.route("/contact")
def contact():
    return render_template("contact.html")


# Download counter
@app.route("/track_download", methods=["GET", "POST"])
def track_download():
    stats_collection.update_one({"name": "main"}, {"$inc": {"downloads": 1}})
    stats = get_stats()
    return jsonify({"status": "success", "new_count": stats["downloads"]})


try:
    from fetch import fetch_media_data
except ModuleNotFoundError:
    from api.fetch import fetch_media_data


# Fetch media URL
@app.route("/ajax_url")
def ajax_url():
    reel_url = request.args.get("ajax_url")
    if not reel_url:
        return jsonify({"status": "error", "message": "Empty URL"})
    if not host_matches(reel_url, ALLOWED_DOMAINS):
        return jsonify({"status": "error", "message": "Unsupported URL"})

    try:
        data = fetch_media_data(reel_url)

        if data.get("status") == "success" and "url" in data:
            qr_id = uuid.uuid4().hex[:8]
            qr_collection.insert_one(
                {"_id": qr_id, "url": data["url"], "created_at": datetime.utcnow()}
            )
            data["qr_id"] = qr_id

            url_log.insert_one({"original_url": reel_url, "at": datetime.utcnow()})
        return jsonify(data)

    except Exception as e:
        print("ajax_url error:", e)
        return jsonify({"status": "error", "message": "Server error, try again."})


# Thumbnail proxy (history ke liye)
@app.route("/thumb")
def thumb():
    u = request.args.get("u", "")
    if not host_matches(u, THUMB_HOSTS):
        return "", 400
    try:
        r = requests.get(
            u,
            timeout=8,
            stream=True,
            allow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        ctype = r.headers.get("Content-Type", "")
        if r.status_code != 200 or not ctype.startswith("image/"):
            return "", 404
        data = r.raw.read(2_000_000, decode_content=True)
        resp = Response(data, mimetype=ctype)
        resp.headers["Cache-Control"] = "public, max-age=3600"
        return resp
    except Exception as e:
        print("thumb error:", e)
        return "", 502


# QR redirect
@app.route("/qr/<qr_id>")
def qr_redirect(qr_id):
    doc = qr_collection.find_one({"_id": qr_id})
    return redirect(doc["url"]) if doc else redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")