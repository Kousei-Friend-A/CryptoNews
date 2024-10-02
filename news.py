import logging
import asyncio
import aiohttp
import feedparser
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Setup logging
logging.basicConfig(level=logging.INFO)

# Your API credentials and channel configuration
API_ID = 8143727
API_HASH = "e2e9b22c6522465b62d8445840a526b1"
BOT_TOKEN = "8150136049:AAH1nLTe3rn80g9ONUbogVD4cUApZenSleY"
CHANNEL_ID = '@CryptoNewsLibrary'  # Your Telegram channel ID
RSS_URL = "https://decrypt.co/feed"  # Decrypt RSS feed
LAST_TITLE_FILE = "last_title.txt"  # File to store the last sent title

# Create a Pyrogram client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def load_last_title():
    """Load the last sent title from a text file."""
    try:
        with open(LAST_TITLE_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None  # Return None if the file doesn't exist

def save_last_title(title):
    """Save the last sent title to a text file."""
    with open(LAST_TITLE_FILE, "w") as file:
        file.write(title)

async def fetch_rss_feed(url):
    """Fetch the RSS feed using aiohttp."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            rss_content = await response.text()
            return feedparser.parse(rss_content)

async def send_latest_feed_to_telegram(last_sent_title):
    """Fetch and send the latest RSS feed to Telegram."""
    # Fetch and parse the RSS feed
    feed = await fetch_rss_feed(RSS_URL)

    if feed.entries:
        latest_entry = feed.entries[0]  # Get the latest entry
        title = latest_entry.title
        description = latest_entry.description

        # Check if the latest title has already been sent
        if title != last_sent_title:
            # Create a message with title and description
            message = f"<b>{title}</b>\n{description}"

            # Send the message to the Telegram channel
            await app.send_message(CHANNEL_ID, message, parse_mode="html")

            # Update the last sent title
            save_last_title(title)

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

async def fetch_and_send_updates():
    """Periodically fetch updates from the RSS feed."""
    last_sent_title = load_last_title()  # Load the last sent title

    while True:
        await send_latest_feed_to_telegram(last_sent_title)
        await asyncio.sleep(60)  # Wait for one minute before checking again

# Main entry point
if __name__ == '__main__':
    with app:
        logging.info("Bot is starting...")
        app.run(fetch_and_send_updates())
