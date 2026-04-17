import discord
import os
import requests
from openai import OpenAI

# 🔐 KEYS
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ⚙️ Discord
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ======================
# READY
# ======================
@bot.event
async def on_ready():
    print("BOT CONNECTÉ")

# ======================
# MESSAGE HANDLER
# ======================
@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    # ======================
    # TEST
    # ======================
    if message.content == "!test":
        await message.channel.send("Bot OK")
        return

    # ======================
    # 🔥 TREND
    # ======================
    if message.content == "!trend":
        await message.channel.send("Scan des tendances retail...")

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Donne les stocks populaires Reddit et Stocktwits."},
                    {"role": "user", "content": "Donne 5 stocks populaires Reddit et 5 Stocktwits."}
                ],
                max_tokens=150
            )

            await message.channel.send(
                "🔥 TREND RETAIL\n\n" +
                response.choices[0].message.content +
                "\n\n⚠️ À valider avec !analyse"
            )

        except:
            await message.channel.send("Erreur trend.")

        return

    # ======================
    # 📊 ANALYSE
    # ======================
    if message.content.startswith("!analyse"):
        ticker = message.content.replace("!analyse", "").strip().upper()

        if ticker == "":
            await message.channel.send("Ex: !analyse AAPL")
            return

        await message.channel.send("Analyse en cours...")

        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/30?adjusted=true&sort=asc&limit=30&apiKey={POLYGON_API_KEY}"
            r = requests.get(url)
            data = r.json()

            if "results" not in data or len(data["results"]) < 20:
                await message.channel.send("Pas assez de données.")
                return

            closes = [c["c"] for c in data["results"]]

            # RSI
            gains = []
            losses = []

            for i in range(1, len(closes)):
                diff = closes[i] - closes[i-1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(diff))

            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            # EMA
            def ema(prices, period):
                multiplier = 2 / (period + 1)
                ema_value = prices[0]

                for price in prices:
                    ema_value = (price - ema_value) * multiplier + ema_value

                return ema_value

            ema9 = ema(closes[-20:], 9)
            ema20 = ema(closes[-20:], 20)

            last_price = closes[-1]

            structure = "haussière" if last_price > ema20 else "fragile"

            if rsi > 60:
                momentum = "fort"
            elif rsi > 50:
                momentum = "positif"
            else:
                momentum = "faible"

            score = 0
            if last_price > ema20:
                score += 30
            if ema9 > ema20:
                score += 25
            if rsi > 50:
                score += 25
            if last_price > ema9:
                score += 20

            if score >= 75:
                bias = "Bullish fort"
            elif score >= 50:
                bias = "Bullish modéré"
            elif score >= 30:
                bias = "Neutre"
            else:
                bias = "Bearish"

            if score >= 70:
                scenario = "continuation haussière"
            elif score >= 50:
                scenario = "consolidation"
            else:
                scenario = "pression baissière"

            probability = int(40 + (score * 0.4))
            if probability > 85:
                probability = 85

            risk = "perte EMA20 = affaiblissement"

            await message.channel.send(
                f"{ticker}\n\n"
                f"Prix: {last_price:.2f}\n"
                f"RSI: {rsi:.1f}\n\n"
                f"EMA9: {ema9:.2f}\n"
                f"EMA20: {ema20:.2f}\n\n"
                f"Structure: {structure}\n"
                f"Momentum: {momentum}\n\n"
                f"Score: {score}/100\n"
                f"Biais: {bias}\n\n"
                f"Scénario: {scenario}\n"
                f"Probabilité: {probability}%\n\n"
                f"Risque: {risk}"
            )

        except:
            await message.channel.send("Erreur analyse.")

        return

    # ======================
    # WHY
    # ======================
    if message.content.startswith("!why"):
        ticker = message.content.replace("!why", "").strip().upper()

        await message.channel.send("Analyse des raisons...")

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Analyste marché"},
                    {"role": "user", "content": f"Pourquoi {ticker} bouge ?"}
                ]
            )

            await message.channel.send(response.choices[0].message.content)

        except:
            await message.channel.send("Erreur why.")

        return

    # ======================
    # NEWS
    # ======================
    if message.content.startswith("!news"):
        ticker = message.content.replace("!news", "").strip().upper()

        await message.channel.send("Recherche news...")

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "News financières"},
                    {"role": "user", "content": f"News importantes pour {ticker}"}
                ]
            )

            await message.channel.send(response.choices[0].message.content)

        except:
            await message.channel.send("Erreur news.")

        return

    # ======================
    # SETUP
    # ======================
    if message.content.startswith("!setup"):
        ticker = message.content.replace("!setup", "").strip().upper()

        await message.channel.send("Analyse setup...")

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Trader pro"},
                    {"role": "user", "content": f"Setup trading pour {ticker}"}
                ]
            )

            await message.channel.send(response.choices[0].message.content)

        except:
            await message.channel.send("Erreur setup.")

        return

    # ======================
    # INFO
    # ======================
    if message.content.startswith("!info"):
        ticker = message.content.replace("!info", "").strip().upper()

        await message.channel.send("Recherche info...")

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Explique entreprise"},
                    {"role": "user", "content": f"Que fait {ticker}"}
                ]
            )

            await message.channel.send(response.choices[0].message.content)

        except:
            await message.channel.send("Erreur info.")

        return

# ======================
# RUN
# ======================
bot.run(DISCORD_TOKEN)
