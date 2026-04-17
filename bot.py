import discord
import os
import requests

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print("BOT CONNECTÉ")

@bot.event
async def on_message(message):
    print("MESSAGE:", message.content)

    if message.author == bot.user:
        return

    # TEST
    if message.content == "!test":
        await message.channel.send("Bot OK")
        return

    # ANALYSE (BIEN INDENTÉE)
   if message.content.startswith("!analyse"):
    ticker = message.content.replace("!analyse", "").strip().upper()

    await message.channel.send("Test Polygon en cours...")

    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/5?adjusted=true&apiKey={POLYGON_API_KEY}"
        r = requests.get(url)

        await message.channel.send(f"Status code: {r.status_code}")

        await message.channel.send(r.text[:500])  # montre réponse brute

    except Exception as e:
        await message.channel.send(f"Erreur: {str(e)}")

bot.run(DISCORD_TOKEN)
