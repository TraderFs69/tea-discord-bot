import discord
import os
import requests
from openai import OpenAI

# ======================
# 🔐 KEYS
# ======================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ======================
# ⚙️ DISCORD
# ======================
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ======================
# 🧠 MEMORY
# ======================
memory = {}

# ======================
# 📰 GDELT NEWS FUNCTION
# ======================
def get_news_gdelt(ticker):
    try:
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={ticker}&mode=artlist&maxrecords=5&format=json"
        r = requests.get(url)
        data = r.json()

        articles = []
        if "articles" in data:
            for a in data["articles"]:
                articles.append(a["title"])

        return articles

    except:
        return []

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
    # 🔥 TREND
    # ======================
    if message.content == "!trend":
        await message.channel.send("Scan des tendances retail...")

        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "Donne les stocks populaires Reddit et Stocktwits."},
                    {"role": "user", "content": "Donne 5 stocks Reddit et 5 Stocktwits."}
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
    # 📊 ANALYSE TECHNIQUE
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
            gains, losses = [], []
            for i in range(1, len(closes)):
                diff = closes[i] - closes[i-1]
                gains.append(diff if diff > 0 else 0)
                losses.append(abs(diff) if diff < 0 else 0)

            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))

            # EMA
            def ema(prices, period):
                m = 2 / (period + 1)
                val = prices[0]
                for p in prices:
                    val = (p - val) * m + val
                return val

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

            probability = min(85, int(40 + score * 0.4))

            await message.channel.send(
                f"{ticker}\n\nPrix: {price:.2f}\nRSI: {rsi:.1f}\n\n"
                f"EMA9: {ema9:.2f}\nEMA20: {ema20:.2f}\n\n"
                f"Structure: {structure}\nMomentum: {momentum}\n\n"
                f"Score: {score}/100\nProbabilité: {probability}%"
            )

        except Exception as e:
            print(e)
            await message.channel.send("Erreur analyse.")

        return

    # ======================
    # 💬 CHAT + NEWS TEMPS RÉEL
    # ======================
    if bot.user in message.mentions:

        question = message.content
        for mention in message.mentions:
            question = question.replace(f"<@{mention.id}>", "")
            question = question.replace(f"<@!{mention.id}>", "")

        question = question.strip()

        if question == "":
            await message.channel.send("Pose-moi une question 😊")
            return

        await message.channel.send("Analyse en cours...")

        if user_id not in memory:
            memory[user_id] = []

        memory[user_id].append({"role": "user", "content": question})
        memory[user_id] = memory[user_id][-10:]

        # 🔥 DETECT TICKER
        words = question.split()
        ticker = None
        for w in words:
            if w.isupper() and len(w) <= 5:
                ticker = w
                break

        news_text = ""
        if ticker:
            news = get_news_gdelt(ticker)
            news_text = "\n".join(news)

        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "system",
                        "content": """Tu es un trader professionnel.

Tu dois identifier la cause PRINCIPALE d’un mouvement.

Méthode :
1. Trouver la news dominante
2. Vérifier le momentum
3. Voir si c’est du positioning ou du fondamental

Réponds comme un trader expérimenté, pas comme un journaliste.
"""
                    },
                    {
                        "role": "user",
                        "content": f"""
Question: {question}

News récentes:
{news_text}

Explique la vraie raison du mouvement.
"""
                    }
                ],
                max_tokens=400
            )

            reply = response.choices[0].message.content

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
