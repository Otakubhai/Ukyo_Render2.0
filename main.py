import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize Pyrogram Bot
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Quality and Format Selection
QUALITY_SELECTION = {}
FORMAT_SELECTION = {}

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
            episodes
            genres
        }
    }
    '''
    variables = {"search": anime_name}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"query": query, "variables": variables}) as response:
            data = await response.json()
            return data.get("data", {}).get("Media")

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome! Use /anime to search anime or /get_doujin to download images.")

@bot.on_message(filters.command("get_doujin"))
async def get_doujin(client, message):
    await message.reply_text("Send me a Multporn link.")

@bot.on_message(filters.command("anime"))
async def anime(client, message):
    await message.reply_text("Enter anime name:")

    @bot.on_message(filters.text & filters.private)
    async def select_quality(client, quality_msg):
        anime_name = quality_msg.text
        QUALITY_SELECTION[quality_msg.chat.id] = anime_name

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("480p", callback_data="480p")],
            [InlineKeyboardButton("720p", callback_data="720p")],
            [InlineKeyboardButton("1080p", callback_data="1080p")],
            [InlineKeyboardButton("720p & 1080p", callback_data="720p_1080p")],
            [InlineKeyboardButton("480p, 720p & 1080p", callback_data="all_qualities")]
        ])
        await quality_msg.reply_text("Choose quality:", reply_markup=keyboard)

@bot.on_callback_query()
async def button_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data in ["480p", "720p", "1080p", "720p_1080p", "all_qualities"]:
        FORMAT_SELECTION[user_id] = data
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Otaku", callback_data="otaku")],
            [InlineKeyboardButton("Hanime", callback_data="hanime")]
        ])
        await callback_query.message.reply_text("Choose format:", reply_markup=keyboard)

    elif data in ["otaku", "hanime"]:
        anime_name = QUALITY_SELECTION.get(user_id)
        quality = FORMAT_SELECTION.get(user_id)
        anime = await fetch_anime_info(anime_name)

        if not anime:
            await callback_query.message.reply_text("Anime not found.")
            return

        anime_id = anime["id"]
        image_url = f"https://img.anili.st/media/{anime_id}"
        genres = ", ".join(anime["genres"])
        episodes = anime["episodes"] or "N/A"

        if data == "hanime":
            message = f"<b>💦 {anime_name}\n" \
                      f"╭──────────────────────\n" \
                      f"├ 📺 Episode : {episodes}\n" \
                      f"├ 💾 Quality : {quality}\n" \
                      f"├ 🎭 Genres: {genres}\n" \
                      f"├ 🔊 Audio track : Sub\n" \
                      f"├ #Censored\n" \
                      f"├ #Recommendation +++++++\n" \
                      f"╰──────────────────────</b>"
        else:
            genre_tags = " ".join([f"#{g}" for g in anime["genres"]])
            message = f"<b>🧡  {anime_name}\n\n" \
                      f"🎭 : {genres}\n" \
                      f"🎨 : Extra Tags\n\n" \
                      f"🔊 : Dual\n" \
                      f"📡 : Season Completed\n" \
                      f"🗓 : {episodes}\n" \
                      f"💾 : {quality}\n" \
                      f"✂️ : 60MB | 300MB | 1GB\n" \
                      f"🔞 : PG-13\n\n" \
                      f"📌 : {genre_tags}</b>"

        await callback_query.message.reply_photo(photo=image_url, caption=message, parse_mode="HTML")

# Start bot
bot.run()
