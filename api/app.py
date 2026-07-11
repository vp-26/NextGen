from flask import Flask, request, jsonify, session, redirect, render_template, g
from pymongo import MongoClient
import json
import uuid
import os
import sys

# absolute path setup (Kyunki app.py root folder mein hai, toh seedhe 'templates' jodenge)
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates') 

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "your_secret_key"

# MongoDB Connection
MONGO_URI = "mongodb+srv://veloradrive83_db_user:prince%40987654@cluster0.5kx2nsr.mongodb.net/VeloraDrive?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["VeloraDrive"]
stats_collection = db["website_stats"]

try:
    client.admin.command("ping")
    print("MongoDB Connected Successfully")
except Exception as e:
    print("MongoDB Connection Error:", e)

if stats_collection.count_documents({"name": "main"}) == 0:
    stats_collection.insert_one(
        {"name": "main", "visitors": 0, "downloads": 0, "urls": []}
    )

# Helper Function
def get_stats():
    stats = stats_collection.find_one({"name": "main"})
    if not stats:
        stats = {"name": "main", "visitors": 0, "downloads": 0, "urls": []}
        stats_collection.insert_one(stats)
    return stats

# Visitor Counter
@app.before_request
def visitor_counter():
    if request.path in ["/ajax_url", "/track_download", "/favicon.ico"]:
        return
    if request.cookies.get("visitor_counted"):
        return
    try:
        stats_collection.update_one({"name": "main"}, {"$inc": {"visitors": 1}})
        g.set_visitor_cookie = True
    except Exception as e:
        print("Error updating visitor count:", e)

@app.after_request
def after_request(response):
    if getattr(g, "set_visitor_cookie", False):
        response.set_cookie(
            "visitor_counted",
            "yes",
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="Lax",
        )
    return response

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
        return f"Error rendering index: {str(e)}", 500

# Contact
@app.route("/contact")
def contact():
    return render_template("contact.html")

# Download Counter
@app.route("/track_download")
def track_download():
    stats_collection.update_one({"name": "main"}, {"$inc": {"downloads": 1}})
    stats = get_stats()
    return jsonify({"status": "success", "new_count": stats["downloads"]})

# Fetch Media URL
@app.route("/ajax_url")
def ajax_url():
    # Agar fetch.py fail ho raha ho toh import path check karein
    try:
        from api.fetch import fetch_media_data
    except ModuleNotFoundError:
        from fetch import fetch_media_data
    
    reel_url = request.args.get("ajax_url")
    if not reel_url:
        return jsonify({"status": "error", "message": "Empty URL"})

    try:
        data = fetch_media_data(reel_url)

        if data.get("status") == "success" and "url" in data:
            qr_id = uuid.uuid4().hex[:8]

            qr_links = session.get("qr_links", {})
            qr_links[qr_id] = data["url"]
            session["qr_links"] = qr_links

            data["qr_id"] = qr_id

            stats_collection.update_one(
                {"name": "main"},
                {"$push": {"urls": {"original_url": reel_url}}},
            )
        return jsonify(data)

    except Exception as e:
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"})

# QR Redirect
@app.route("/qr/<qr_id>")
def qr_redirect(qr_id):
    clear_links = session.get("qr_links", {})
    if qr_id in clear_links:
        return redirect(clear_links[qr_id])
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)