import os
import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")

bot = Client("anime_multporn_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User session storage
QUALITY_SELECTION = {}
FORMAT_SELECTION = {}
AWAITING_MULTPORN_LINK = {}

async def fetch_anime_info(anime_name):
    """Fetch anime details from AniList API"""
    url = "https://graphql.anilist.co/"
    query = '''
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            id
            title {
                romaji
                english
            }
            description
            episodes
            genres
            duration
            averageScore
            season
            seasonYear
            coverImage {
                extraLarge
            }
            tags {
                name
            }
        }
    }
    '''
    variables = {"search": anime_name}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"query": query, "variables": variables}) as response:
            data = await response.json()
            return data.get("data", {}).get("Media")

async def download_images_from_multporn(url):
    """Download all images from a Multporn link"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            
            html_content = await response.text()
    
    soup = BeautifulSoup(html_content, 'lxml')
    image_elements = soup.select('.jb-image img')
    image_urls = []

    for img in image_elements:
        if 'src' in img.attrs:
            image_url = img['src']
            if not image_url.startswith('http'):
                image_url = 'https://multporn.net' + image_url
            image_urls.append(image_url)
    
    return image_urls

@bot.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)
    
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await message.reply_text("You are not authorized to use this bot.")
        return
    
    await message.reply_text("Welcome! Use /anime to search for anime info or /get_doujin to download images from Multporn.")

@bot.on_message(filters.command("get_doujin"))
async def get_doujin(client, message):
    user_id = str(message.from_user.id)
    
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await message.reply_text("You are not authorized to use this bot.")
        return
    
    AWAITING_MULTPORN_LINK[message.chat.id] = True
    await message.reply_text("Please send me a Multporn link.")

@bot.on_message(filters.command("anime"))
async def anime(client, message):
    user_id = str(message.from_user.id)
    
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await message.reply_text("You are not authorized to use this bot.")
        return
    
    await message.reply_text("Enter anime name:")
    QUALITY_SELECTION[message.chat.id] = None

@bot.on_message(filters.text & filters.private)
async def handle_text(client, message):
    chat_id = message.chat.id
    
    if chat_id in AWAITING_MULTPORN_LINK and AWAITING_MULTPORN_LINK[chat_id]:
        if re.match(r'https?://multporn\.net/\S+', message.text):
            await process_multporn_link(client, message)
            AWAITING_MULTPORN_LINK[chat_id] = False
            return
        else:
            await message.reply_text("Invalid Multporn link. Please send a valid link from multporn.net")
            return
    
    if chat_id in QUALITY_SELECTION and QUALITY_SELECTION[chat_id] is None:
        anime_name = message.text
        QUALITY_SELECTION[chat_id] = anime_name

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("480p", callback_data="480p")],
            [InlineKeyboardButton("720p", callback_data="720p")],
            [InlineKeyboardButton("1080p", callback_data="1080p")],
            [InlineKeyboardButton("720p & 1080p", callback_data="720p_1080p")],
            [InlineKeyboardButton("480p, 720p & 1080p", callback_data="all_qualities")]
        ])
        await message.reply_text("Choose quality:", reply_markup=keyboard)

async def process_multporn_link(client, message):
    """Process the multporn link and download images"""
    url = message.text
    await message.reply_text(f"Downloading images from {url}...")
    
    image_urls = await download_images_from_multporn(url)
    
    if not image_urls:
        await message.reply_text("No images found or invalid URL.")
        return
    
    for i, img_url in enumerate(image_urls):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        await client.send_document(
                            chat_id=message.chat.id,
                            document=content,
                            file_name=f"image_{i+1}.jpg",
                            caption=f"Image {i+1}/{len(image_urls)}"
                        )
                        await asyncio.sleep(1)
        except Exception as e:
            await message.reply_text(f"Error uploading image {i+1}: {str(e)}")

@bot.on_callback_query()
async def button_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data

    if data in ["480p", "720p", "1080p", "720p_1080p", "all_qualities"]:
        FORMAT_SELECTION[chat_id] = data
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Otaku", callback_data="otaku")],
            [InlineKeyboardButton("Hanime", callback_data="hanime")]
        ])
        await callback_query.message.reply_text("Choose format:", reply_markup=keyboard)

    elif data in ["otaku", "hanime"]:
        anime_name = QUALITY_SELECTION.get(chat_id)
        quality = FORMAT_SELECTION.get(chat_id)
        QUALITY_SELECTION[chat_id] = None

        anime = await fetch_anime_info(anime_name)

        if not anime:
            await callback_query.message.reply_text("Anime not found.")
            return

        anime_id = anime["id"]
        image_url = f"https://img.anili.st/media/{anime_id}"
        title = anime["title"]["english"] or anime["title"]["romaji"]
        genres_text = ", ".join(anime["genres"])
        episodes = anime["episodes"] or "N/A"

        if data == "hanime":
            message = f"<b>💦 {title}\n📺 Episode: {episodes}\n💾 Quality: {quality}\n🎭 Genres: {genres_text}\n🔊 Audio track: Sub\n#Censored\n#Recommendation +++++++</b>"
        else:
            genre_tags = " ".join([f"#{g}" for g in anime["genres"]])
            message = f"<b>🧡 {title}\n🎭 {genres_text}\n🔊 Dual\n📡 Season Completed\n🗓 {episodes}\n💾 {quality}\n✂️ 60MB | 300MB | 1GB\n📌 {genre_tags}</b>"

        await client.send_photo(chat_id=chat_id, photo=image_url, caption=message, parse_mode=ParseMode.HTML)

print("Bot is running...")
bot.run()
