import discord
import os
import requests

print("VERSION TEST 12345")

# 🔐 Clés
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# ⚙️ Discord setup
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# ======================
# 🤖 BOT READY
# ======================
@bot.event
async def on_ready():
    print(f"BOT CONNECTÉ: {bot.user}")

# ======================
# 💬 MESSAGE HANDLER
# ======================
@bot.event
async def on_message(message):
    print("MESSAGE:", message.content)

    if message.author == bot.user:
        return

    if message.content == "!test":
        await message.channel.send("Bot OK")
        return

    if message.content.startswith("!analyse"):
    ticker = message.content.replace("!analyse", "").strip().upper()

    if ticker == "":
        await message.channel.send("Ex: !analyse AAPL")
        return

    await message.channel.send(f"Récupération des données pour {ticker}...")

    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/30?adjusted=true&apiKey={POLYGON_API_KEY}"
        r = requests.get(url)

        print("STATUS CODE:", r.status_code)

        text = r.text
        print("RAW RESPONSE:", text)

        data = r.json()

        if "results" not in data:
            await message.channel.send("Erreur Polygon ou clé API invalide.")
            return

        closes = [c["c"] for c in data["results"]]
        last_price = closes[-1]

        await message.channel.send(f"{ticker} prix actuel: {last_price:.2f}")

    except Exception as e:
        print("ERREUR:", str(e))
        await message.channel.send("Erreur analyse.")
        
# 🚀 Lancement
bot.run(DISCORD_TOKEN)
