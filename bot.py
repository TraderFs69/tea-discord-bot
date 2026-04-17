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

memory = {}

# ======================
# 📰 GDELT + SMART FILTER
# ======================
def get_filtered_news(ticker):
    try:
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={ticker}&mode=artlist&maxrecords=10&format=json"
        r = requests.get(url)
        data = r.json()

        if "articles" not in data:
            return []

        keywords = [
            "earnings", "guidance", "forecast", "upgrade",
            "downgrade", "deal", "acquisition", "AI",
            "revenue", "profit", "lawsuit", "partnership"
        ]

        filtered = []

        for a in data["articles"]:
            title = a["title"].lower()

            if any(k in title for k in keywords):
                filtered.append(a["title"])

        return filtered[:5]

    except:
        return []

# ======================
# READY
# ======================
@bot.event
async def on_ready():
    print("BOT CONNECTÉ")

# ======================
# MESSAGE
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

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Stocks populaires Reddit et Stocktwits"},
                {"role": "user", "content": "Donne 5 stocks Reddit et 5 Stocktwits"}
            ]
        )

        await message.channel.send("🔥 TREND RETAIL\n\n" +
            response.choices[0].message.content +
            "\n\n⚠️ À valider avec !analyse")

        return

    # ======================
    # ANALYSE
    # ======================
    if message.content.startswith("!analyse"):
        ticker = message.content.replace("!analyse", "").strip().upper()

        await message.channel.send("Analyse en cours...")

        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/30?adjusted=true&sort=asc&limit=30&apiKey={POLYGON_API_KEY}"
            data = requests.get(url).json()

            closes = [c["c"] for c in data["results"]]

            gains, losses = [], []
            for i in range(1, len(closes)):
                diff = closes[i] - closes[i-1]
                gains.append(diff if diff > 0 else 0)
                losses.append(abs(diff) if diff < 0 else 0)

            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain/avg_loss))

            def ema(prices, period):
                m = 2/(period+1)
                val = prices[0]
                for p in prices:
                    val = (p - val)*m + val
                return val

            ema9 = ema(closes[-20:], 9)
            ema20 = ema(closes[-20:], 20)
            price = closes[-1]

            score = 0
            if price > ema20: score += 30
            if ema9 > ema20: score += 25
            if rsi > 50: score += 25
            if price > ema9: score += 20

            prob = min(85, int(40 + score*0.4))

            await message.channel.send(
                f"{ticker}\nPrix: {price:.2f}\nRSI: {rsi:.1f}\n"
                f"EMA9: {ema9:.2f} | EMA20: {ema20:.2f}\n"
                f"Score: {score}/100 | Probabilité: {prob}%"
            )

        except:
            await message.channel.send("Erreur analyse.")

        return

    # ======================
    # 💬 CHAT SMART FILTER
    # ======================
    if bot.user in message.mentions:

        question = message.content
        for mention in message.mentions:
            question = question.replace(f"<@{mention.id}>", "")
            question = question.replace(f"<@!{mention.id}>", "")

        question = question.strip()

        await message.channel.send("Analyse en cours...")

        if user_id not in memory:
            memory[user_id] = []

        memory[user_id].append({"role": "user", "content": question})
        memory[user_id] = memory[user_id][-10:]

        # 🔥 detect ticker
        ticker = None
        for word in question.split():
            if word.isupper() and len(word) <= 5:
                ticker = word
                break

        news = get_filtered_news(ticker) if ticker else []

        if len(news) == 0:
            news_text = "Aucune news pertinente trouvée."
        else:
            news_text = "\n".join(news)

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": """Tu es un trader professionnel.

Tu dois identifier la cause réelle d’un mouvement.

Règles :
- Ne jamais inventer
- Si aucune news → dire que c’est du momentum
- Toujours distinguer news vs positioning vs technique
- Répondre comme un trader réel
"""
                },
                {
                    "role": "user",
                    "content": f"""
Question: {question}

News:
{news_text}

Explique la vraie cause.
"""
                }
            ],
            max_tokens=400
        )

        reply = response.choices[0].message.content

        memory[user_id].append({"role": "assistant", "content": reply})

        await message.channel.send(reply)

        return

# ======================
# RUN
# ======================
bot.run(DISCORD_TOKEN)
