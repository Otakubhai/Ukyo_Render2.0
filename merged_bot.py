import os
import tempfile
import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from PIL import Image
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import gc

# Import PDF generation function
from pdf_generator import create_pdf

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetch bot token
TOKEN = os.getenv("BOT_TOKEN")

# Use temp directory instead of persistent storage
TEMP_DIR = tempfile.gettempdir()

# Define conversation states
QUALITY_SELECTION, SYNOPSIS = range(2)

async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command"""
    await update.message.reply_text(
        "Hey there! Use this bot to:\n"
        "- Get anime posts: `/anime <name>`\n"
        "- Download doujins: `/get_doujin <URL>`"
    )

# ANIME POST HANDLER
async def anime(update: Update, context: CallbackContext) -> None:
    """Handles the /anime command."""
    if not context.args:
        await update.message.reply_text("Please provide an anime name.")
        return

    anime_name = " ".join(context.args)
    anime_data = await get_anime_info(anime_name)

    if anime_data:
        await update.message.reply_photo(photo=anime_data["image_url"], caption=anime_data["caption"], parse_mode="Markdown")
    else:
        await update.message.reply_text("Anime not found or an error occurred.")

async def get_anime_info(anime_name: str) -> dict | None:
    """Fetch anime details from AniList API."""
    url = "https://graphql.anilist.co/"
    query = '''
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            title { romaji english }
            episodes genres coverImage { extraLarge }
        }
    }
    '''
    variables = {"search": anime_name}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"query": query, "variables": variables}) as response:
            if response.status == 200:
                data = await response.json()
                anime_data = data.get("data", {}).get("Media")

                if anime_data:
                    title = anime_data["title"]["english"] or anime_data["title"]["romaji"]
                    genres = ", ".join(["Hanime"] + anime_data["genres"])
                    image_url = anime_data["coverImage"]["extraLarge"]

                    caption = (
                        f"💦 {title}\\n"
                        "╭──────────────────────\\n"
                        f"├ 📺 Episode : {anime_data['episodes']}\\n"
                        "├ 💾 Quality : 720p\\n"
                        f"├ 🎭 Genres: {genres}\\n"
                        "├ 🔊 Audio track : Sub\\n"
                        "├ #Censored\\n"
                        "├ #Recommendation +++++++\\n"
                        "╰──────────────────────"
                    )

                    return {"image_url": image_url, "caption": caption}

    return None

# DOUJIN DOWNLOAD HANDLER
async def get_doujin(update: Update, context: CallbackContext) -> None:
    """Handles the /get_doujin command."""
    if not context.args:
        await update.message.reply_text("Please provide a valid Multporn.net URL.")
        return
    
    url = context.args[0].strip()
    if "multporn.net" not in url:
        await update.message.reply_text("Invalid URL. Please send a valid Multporn.net link.")
        return

    await update.message.reply_text("Fetching images... Please wait.")
    
    try:
        image_urls = scrape_images(url)
        if not image_urls:
            await update.message.reply_text("No images found or invalid URL.")
            return

        # Download images
        image_paths = download_images(image_urls)

        if not image_paths:
            await update.message.reply_text("Failed to download images.")
            return

        # Generate PDF
        pdf_path = os.path.join(TEMP_DIR, "doujin.pdf")
        create_pdf(image_paths, pdf_path)

        # Send PDF to user
        with open(pdf_path, "rb") as pdf_file:
            await update.message.reply_document(document=InputFile(pdf_file, filename="doujin.pdf"), caption="Here is your doujin PDF.")

    except Exception as e:
        logger.error(f"Error processing doujin: {e}")
        await update.message.reply_text("An error occurred while processing the request.")
    finally:
        gc.collect()

def scrape_images(url: str):
    """Scrapes all image URLs from the given Multporn.net page."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    image_tags = soup.find_all("img")

    image_urls = []
    for img in image_tags:
        src = img.get("src")
        if src and "uploads" in src:
            if not src.startswith("http"):
                src = "https://multporn.net" + src
            image_urls.append(src)

    return image_urls

def download_images(image_urls):
    """Downloads images and returns a list of local file paths."""
    image_paths = []
    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                img_path = os.path.join(TEMP_DIR, f"image_{i}.jpg")
                with open(img_path, "wb") as img_file:
                    for chunk in response.iter_content(1024):
                        img_file.write(chunk)
                image_paths.append(img_path)
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")

    return image_paths

def main() -> None:
    """Main function to run the bot."""
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("anime", anime, pass_args=True))
    app.add_handler(CommandHandler("get_doujin", get_doujin, pass_args=True))
    
    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
