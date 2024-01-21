from flask import Flask, render_template, request, redirect, url_for
import feedparser
from datetime import datetime
import schedule
import time
from dateutil import parser as date_parser

app = Flask(__name__)

# List of cybersecurity news RSS feed URLs
rss_feeds = [
    "https://krebsonsecurity.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.mcafee.com/blogs/feed/","https://www.bleepingcomputer.com/feed/","https://blog.malwarebytes.com/feed/","https://cyble.com/blog/feed/","https://www.sentinelone.com/feed/","https://www.bitdefender.com/blog/api/rss/labs/","https://any.run/cybersecurity-blog/category/malware-analysis/feed/"
    # Add more feed URLs as needed
]

latest_updates = []
last_updated_time = None


def get_latest_updates():
    global last_updated_time

    all_entries = []
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        new_entries = [
            {
                "title": entry.title,
                "link": entry.link,
                "description": entry.summary,
                "thumbnail": get_thumbnail(entry),
                "published": date_parser.parse(entry.published),
                "source": feed_url,
            }
            for entry in feed.entries
            if entry.link not in [upd["link"] for upd in all_entries]
        ]
        all_entries.extend(new_entries)

    # Sort all entries based on publication time in descending order
    all_entries.sort(key=lambda x: x["published"], reverse=True)
    last_updated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return all_entries


def get_thumbnail(entry):
    # Extract thumbnail URL if available
    media_content = entry.get("media_content", [])
    if media_content:
        return media_content[0]["url"]
    return None


def update_data():
    global latest_updates
    global last_updated_time
    latest_updates = get_latest_updates()
    print("Data updated")


def force_update():
    print("Force updating data...")
    update_data()


def schedule_updates():
    # Schedule the updates every 30 minutes
    schedule.every(30).minutes.do(update_data)
    # Schedule a force update every 6 hours (adjust as needed)
    schedule.every(6).hours.do(force_update)


@app.route("/")
def dashboard():
    global last_updated_time
    global latest_updates

    # Get the latest updates
    latest_updates = get_latest_updates()

    # Create a dictionary to store source information
    source_info = {}

    for entry in latest_updates:
        source = entry["source"]
        if source not in source_info:
            source_info[source] = {
                "count": 1,
                "last_update": entry["published"],
            }
        else:
            source_info[source]["count"] += 1
            if entry["published"] > source_info[source]["last_update"]:
                source_info[source]["last_update"] = entry["published"]

    return render_template("dashboard.html", last_updated_time=last_updated_time, updates=latest_updates, source_info=source_info)


# ... (rest of the code remains unchanged)
@app.route("/update-feeds", methods=["POST"])
def update_feeds():
    new_feed = request.form.get("new_feed")
    if new_feed:
        rss_feeds.append(new_feed)
    return redirect(url_for("dashboard"))


@app.route("/force-update")
def force_update_route():
    force_update()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    # Initialize the data
    update_data()

    # Schedule periodic updates
    schedule_updates()

    # Start the Flask app
    app.run(host="0.0.0.0",debug=True,threaded=True)
