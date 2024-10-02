import os
import feedparser
import aiohttp
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
import re
from dateutil import parser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set your configuration here
API_ID = 8143727
API_HASH = "e2e9b22c6522465b62d8445840a526b1"
BOT_TOKEN = "8150136049:AAH1nLTe3rn80g9ONUbogVD4cUApZenSleY"
CHANNEL_ID = '@CryptoNewsLibrary'  # Replace with your channel ID
RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"  # Coindesk RSS feed

# Paths for storing state
LAST_SENT_TIMESTAMP_FILE = "last_sent_timestamp.txt"
SENT_UPDATES_FILE = "sent_updates.txt"

# Initialize the Pyrogram client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Load last sent timestamp
def load_last_sent_timestamp():
    if os.path.exists(LAST_SENT_TIMESTAMP_FILE):
        with open(LAST_SENT_TIMESTAMP_FILE, 'r') as file:
            return parser.parse(file.read().strip())
    return None

# Save the last sent timestamp
def save_last_sent_timestamp(timestamp):
    with open(LAST_SENT_TIMESTAMP_FILE, 'w') as file:
        file.write(timestamp.isoformat())

# Load sent updates from a file
def load_sent_updates():
    if os.path.exists(SENT_UPDATES_FILE):
        with open(SENT_UPDATES_FILE, 'r') as file:
            return set(line.strip() for line in file)
    return set()

# Save a new sent update
def save_sent_update(title):
    with open(SENT_UPDATES_FILE, 'a') as file:
        file.write(title + '\n')

# Async function to fetch and send updates
async def fetch_and_send_updates():
    last_sent_timestamp = load_last_sent_timestamp()
    sent_updates = load_sent_updates()  # Load previously sent updates

    while True:
        try:
            logging.info("Fetching RSS feed...")
            feed = feedparser.parse(RSS_URL)

            new_updates_count = 0
            latest_entries = []

            for entry in feed.entries:
                # Log the entry for debugging
                logging.debug(f"Feed Entry: {entry}")
                
                # Get the publication date and title
                published = parser.parse(entry.pubDate) if hasattr(entry, 'pubDate') else None
                title = entry.title
                guid = entry.guid if hasattr(entry, 'guid') else title  # Use GUID or title if GUID is missing

                # Add entry to the list to send if not already sent
                if guid not in sent_updates:
                    latest_entries.append(entry)

            for entry in latest_entries:
                title = entry.title
                guid = entry.guid if hasattr(entry, 'guid') else title
                published = parser.parse(entry.pubDate) if hasattr(entry, 'pubDate') else None

                # Check if the update is new
                if published and (last_sent_timestamp is None or published > last_sent_timestamp):
                    last_sent_timestamp = max(last_sent_timestamp, published) if last_sent_timestamp else published
                    save_last_sent_timestamp(last_sent_timestamp)

                    # Format the message to send
                    description = entry.description if hasattr(entry, 'description') else "No description available."
                    message = f"**{title}**\n\n{description}\n\n[Read More]({entry.link})"

                    # Send the entry
                    await app.send_message(
                        chat_id=CHANNEL_ID,
                        text=message,
                        disable_web_page_preview=True
                    )
                    logging.info(f"Sent update with title: {title}")

                    # Mark this update as sent
                    sent_updates.add(guid)
                    save_sent_update(guid)  # Store the GUID or title of the sent update
                    new_updates_count += 1

            if new_updates_count > 0:
                logging.info(f"Sent {new_updates_count} updates.")
            else:
                logging.info("No new updates found.")

            await asyncio.sleep(60)  # Wait for a minute before fetching again

        except FloodWait as e:
            logging.warning(f"Flood wait triggered. Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            await asyncio.sleep(60)

# Handler for the /start command
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    logging.info(f"Start command received from {message.chat.id}")
    button = InlineKeyboardMarkup([[InlineKeyboardButton("Visit Channel", url="https://t.me/CryptoNewsLibrary")]])
    await app.send_message(
        chat_id=message.chat.id,
        text="Welcome to the Crypto News Bot! Updates will be sent to the channel.",
        reply_markup=button
    )

# Main entry point
if __name__ == '__main__':
    with app:
        logging.info("Bot is starting...")
        app.run(fetch_and_send_updates())
