import discord
import os
import requests

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

            data = r.json()
            print("DATA:", data)

            # 🔥 CHECK 1 : clé API
            if "status" in data and data["status"] == "ERROR":
                await message.channel.send("Erreur Polygon API (clé ou accès).")
                return

            # 🔥 CHECK 2 : pas de résultats
            if "results" not in data or len(data["results"]) == 0:
                await message.channel.send("Aucune donnée disponible pour ce ticker.")
                return

            closes = [c["c"] for c in data["results"]]
            last_price = closes[-1]

            await message.channel.send(f"{ticker} prix actuel: {last_price:.2f}")

        except Exception as e:
            print("ERREUR:", e)
            await message.channel.send("Erreur analyse.")

# 🚀 Lancement
bot.run(DISCORD_TOKEN)
