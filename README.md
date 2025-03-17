# Anime & Multporn Telegram Bot

A Telegram bot with dual functionality:
1. Search for anime information with customizable output formats
2. Download and upload images from Multporn.net

## Features

### Anime Search
- Search for anime by name
- Select quality options (480p, 720p, 1080p, etc.)
- Choose between two output formats: "Otaku" or "Hanime"
- Fetches anime information from AniList API
- Includes images, episodes, genres, and more

### Multporn Downloader
- Download all images from a Multporn.net link
- Images are uploaded as documents to preserve quality
- Progress tracking during uploads

## Deployment on Render

This bot is optimized for deployment on Render's free tier (512MB RAM, 0.1 CPU).

### Prerequisites

1. Create a Telegram bot using [BotFather](https://t.me/BotFather) and get your Bot Token
2. Create an application on [my.telegram.org](https://my.telegram.org/apps) to get API_ID and API_HASH
3. Have a Render account

### Deployment Steps

1. Fork this repository or create a new one with these files
2. Log in to your Render account
3. Click on "New" and select "Web Service"
4. Connect your GitHub repository
5. Configure the web service:
   - **Name**: Choose a name for your service
   - **Environment**: Select "Python 3"
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: Free (512MB RAM, 0.1 CPU)

6. Add environment variables:
   - `API_ID`: Your Telegram API ID (from my.telegram.org)
   - `API_HASH`: Your Telegram API Hash (from my.telegram.org)
   - `BOT_TOKEN`: Your Telegram Bot Token (from BotFather)
   - `ALLOWED_USERS`: Comma-separated list of Telegram user IDs allowed to use the bot (leave empty to allow all users)

7. Click "Create Web Service"

The bot should be up and running within a few minutes!

## Usage

### Anime Search
1. Start the bot and send `/anime` command
2. Enter the anime name when prompted
3. Select quality from the options provided
4. Choose between "Otaku" or "Hanime" format
5. The bot will sen
