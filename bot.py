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

# 🧠 MÉMOIRE PAR UTILISATEUR
memory = {}

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

    user_id = str(message.author.id)

    # ======================
    # TEST
    # ======================
    if message.content == "!test":
        await message.channel.send("Bot OK")
        return

    # ======================
    # TREND
    # ======================
    if message.content == "!trend":
        await message.channel.send("Scan des tendances retail...")

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Donne les stocks populaires Reddit et Stocktwits."},
                    {"role": "user", "content": "Donne 5 stocks Reddit et 5 Stocktwits."}
                ],
                max_tokens=150
            )

            await message.channel.send("🔥 TREND RETAIL\n\n" +
                                       response.choices[0].message.content +
                                       "\n\n⚠️ À valider avec !analyse")
        except:
            await message.channel.send("Erreur trend.")

        return

    # ======================
    # ANALYSE
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

            rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))

            # EMA
            def ema(prices, period):
                multiplier = 2 / (period + 1)
                ema_val = prices[0]
                for p in prices:
                    ema_val = (p - ema_val) * multiplier + ema_val
                return ema_val

            ema9 = ema(closes[-20:], 9)
            ema20 = ema(closes[-20:], 20)
            price = closes[-1]

            structure = "haussière" if price > ema20 else "fragile"
            momentum = "fort" if rsi > 60 else "positif" if rsi > 50 else "faible"

            score = 0
            if price > ema20: score += 30
            if ema9 > ema20: score += 25
            if rsi > 50: score += 25
            if price > ema9: score += 20

            bias = "Bullish fort" if score >= 75 else "Bullish modéré" if score >= 50 else "Neutre" if score >= 30 else "Bearish"
            scenario = "continuation haussière" if score >= 70 else "consolidation" if score >= 50 else "pression baissière"

            probability = min(85, int(40 + score * 0.4))

            await message.channel.send(
                f"{ticker}\n\nPrix: {price:.2f}\nRSI: {rsi:.1f}\n\n"
                f"EMA9: {ema9:.2f}\nEMA20: {ema20:.2f}\n\n"
                f"Structure: {structure}\nMomentum: {momentum}\n\n"
                f"Score: {score}/100\nBiais: {bias}\n\n"
                f"Scénario: {scenario}\nProbabilité: {probability}%"
            )

        except:
            await message.channel.send("Erreur analyse.")

        return

    # ======================
    # CHAT AVEC MÉMOIRE (MENTION)
    # ======================
    if bot.user in message.mentions:

        question = message.content.replace(f"<@{bot.user.id}>", "")
        question = question.replace(f"<@!{bot.user.id}>", "").strip()

        if question == "":
            await message.channel.send("Pose-moi une question 😊")
            return

        await message.channel.send("Réflexion...")

        # 🔥 MÉMOIRE
        if user_id not in memory:
            memory[user_id] = []

        memory[user_id].append({"role": "user", "content": question})

        # Limite mémoire (10 messages)
        memory[user_id] = memory[user_id][-10:]

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Tu es un trader professionnel style TEA.

Règles :
- Pas de bullshit
- Réponse courte, directe
- Toujours orienté décision
- Toujours parler en probabilité
- Prioriser structure, momentum, contexte

Style :
- Punchy
- Clair
- Trading mindset
"""
                    }
                ] + memory[user_id],
                max_tokens=200
            )

            reply = response.choices[0].message.content

            # Sauvegarde réponse
            memory[user_id].append({"role": "assistant", "content": reply})

            await message.channel.send(reply)

        except Exception as e:
            print(e)
            await message.channel.send("Erreur réponse.")

        return

# ======================
# RUN
# ======================
bot.run(DISCORD_TOKEN)
