import os
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetch bot token from environment variables
TOKEN = os.getenv("BOT_TOKEN")

# Define states for conversation
QUALITY_SELECTION, FORMAT_SELECTION = range(2)

# Initialize bot application
app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command"""
    await update.message.reply_text("Welcome! Use /anime to search anime or /get_doujin to download images.")

async def get_doujin(update: Update, context: CallbackContext) -> None:
    """Handles /get_doujin command, asks for Multporn link"""
    await update.message.reply_text("Send me a Multporn link.")

async def anime(update: Update, context: CallbackContext) -> int:
    """Handles /anime command, asks for anime name"""
    await update.message.reply_text("Enter anime name:")
    return QUALITY_SELECTION

async def select_quality(update: Update, context: CallbackContext) -> int:
    """Asks user to select quality"""
    anime_name = update.message.text
    context.user_data["anime_name"] = anime_name

    keyboard = [
        [InlineKeyboardButton("480p", callback_data="480p")],
        [InlineKeyboardButton("720p", callback_data="720p")],
        [InlineKeyboardButton("1080p", callback_data="1080p")],
        [InlineKeyboardButton("720p & 1080p", callback_data="720p_1080p")],
        [InlineKeyboardButton("480p, 720p & 1080p", callback_data="all_qualities")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose quality:", reply_markup=reply_markup)
    return FORMAT_SELECTION

async def format_selection(update: Update, context: CallbackContext) -> None:
    """Asks user to choose Otaku or Hanime format"""
    query = update.callback_query
    context.user_data["quality"] = query.data

    keyboard = [
        [InlineKeyboardButton("Otaku", callback_data="otaku")],
        [InlineKeyboardButton("Hanime", callback_data="hanime")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Choose format:", reply_markup=reply_markup)

async def fetch_anime_info(anime_name: str):
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
        }
    }
    '''
    variables = {"search": anime_name}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"query": query, "variables": variables}) as response:
            data = await response.json()
            anime = data.get("data", {}).get("Media")
            return anime

async def send_anime_info(update: Update, context: CallbackContext) -> None:
    """Send anime info in selected format"""
    query = update.callback_query
    format_choice = query.data
    anime_name = context.user_data["anime_name"]
    quality = context.user_data["quality"]
    
    anime = await fetch_anime_info(anime_name)
    if not anime:
        await query.message.reply_text("Anime not found.")
        return

    anime_id = anime["id"]
    image_url = f"https://img.anili.st/media/{anime_id}"
    genres = ", ".join(anime["genres"])
    episodes = anime["episodes"] or "N/A"
    
    if format_choice == "hanime":
        message = f"<b>💦 {anime_name}
"                   f"╭──────────────────────
"                   f"├ 📺 Episode : {episodes}
"                   f"├ 💾 Quality : {quality}
"                   f"├ 🎭 Genres: {genres}
"                   f"├ 🔊 Audio track : Sub
"                   f"├ #Censored
"                   f"├ #Recommendation +++++++
"                   f"╰──────────────────────</b>"
    else:
        genre_tags = " ".join([f"#{g}" for g in anime["genres"]])
        message = f"<b>🧡  {anime_name}

"                   f"🎭 : {genres}
"                   f"🎨 : Extra Tags

"                   f"🔊 : Dual
"                   f"📡 : Season Completed
"                   f"🗓 : {episodes}
"                   f"💾 : {quality}
"                   f"✂️ : 60MB | 300MB | 1GB
"                   f"🔞 : PG-13

"                   f"📌 : {genre_tags}</b>"
    
    await query.message.reply_photo(photo=image_url, caption=message, parse_mode="HTML")

# Register handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("get_doujin", get_doujin))

anime_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("anime", anime)],
    states={
        QUALITY_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_quality)],
        FORMAT_SELECTION: [CallbackQueryHandler(format_selection), CallbackQueryHandler(send_anime_info)],
    },
    fallbacks=[],
)

app.add_handler(anime_conv_handler)

# Start bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
