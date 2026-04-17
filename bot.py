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

    # ANALYSE (VERSION MASSIVE/POLYGON SIMPLE)
    if message.content.startswith("!analyse"):
        ticker = message.content.replace("!analyse", "").strip().upper()

        if ticker == "":
            await message.channel.send("Ex: !analyse AAPL")
            return

        await message.channel.send("Test API en cours...")

        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?apiKey={POLYGON_API_KEY}"
            r = requests.get(url)

            await message.channel.send(f"Status code: {r.status_code}")

            data = r.json()

            if "results" not in data or len(data["results"]) == 0:
                await message.channel.send("Aucune donnée disponible.")
                return

            last_price = data["results"][0]["c"]

            await message.channel.send(f"{ticker} prix actuel: {last_price:.2f}")

        except Exception as e:
            await message.channel.send(f"Erreur: {str(e)}")

bot.run(DISCORD_TOKEN)
