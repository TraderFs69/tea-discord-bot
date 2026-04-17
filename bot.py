import discord
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

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

    # ANALYSE SIMPLE
    if message.content.startswith("!analyse"):
        ticker = message.content.replace("!analyse", "").strip().upper()

        if ticker == "":
            await message.channel.send("Ex: !analyse TSLA")
            return

        await message.channel.send(f"Récupération des données pour {ticker}...")

        try:
            import requests

            POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/30?adjusted=true&apiKey={POLYGON_API_KEY}"
            r = requests.get(url)
            data = r.json()

            if "results" not in data:
                await message.channel.send("Erreur données.")
                return

            closes = [c["c"] for c in data["results"]]
            last_price = closes[-1]

            await message.channel.send(f"{ticker} prix actuel: {last_price:.2f}")

        except Exception as e:
            print("ERREUR:", e)
            await message.channel.send("Erreur analyse.")

bot.run(DISCORD_TOKEN)
