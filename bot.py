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
# 🧠 NEWS SCORING
# ======================
def score_news(title):
    t = title.lower()
    score = 0

    if any(k in t for k in ["earnings", "guidance", "forecast"]):
        score += 5
    if any(k in t for k in ["deal", "contract", "partnership", "ai", "meta"]):
        score += 5
    if any(k in t for k in ["acquisition", "merger"]):
        score += 5
    if any(k in t for k in ["upgrade", "downgrade"]):
        score += 3
    if any(k in t for k in ["revenue", "profit"]):
        score += 3
    if any(k in t for k in ["opinion", "analysis", "watch", "outlook"]):
        score -= 2

    return score


def get_best_news(ticker):
    try:
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={ticker}&mode=artlist&maxrecords=10&format=json"
        data = requests.get(url).json()

        if "articles" not in data:
            return None, []

        best = None
        best_score = 0
        titles = []

        for a in data["articles"]:
            title = a["title"]
            titles.append(title)

            s = score_news(title)
            if s > best_score:
                best_score = s
                best = title

        return best if best_score > 0 else None, titles

    except:
        return None, []

# ======================
# 🐦 TWITTER SENTIMENT (proxy)
# ======================
def get_twitter_sentiment(titles):

    combined = " ".join(titles).lower()

    bullish_words = ["buy", "bull", "moon", "breakout", "strong", "rally"]
    bearish_words = ["sell", "bear", "dump", "crash", "weak"]

    bull_score = sum(combined.count(w) for w in bullish_words)
    bear_score = sum(combined.count(w) for w in bearish_words)

    if bull_score > bear_score:
        return "bullish"
    elif bear_score > bull_score:
        return "bearish"
    else:
        return "neutral"

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
    # ANALYSE TECHNIQUE
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
    # 💬 CHAT + NEWS + SENTIMENT
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

        # detect ticker
        ticker = None
        for w in question.split():
            if w.isupper() and len(w) <= 5:
                ticker = w
                break

        best_news, titles = get_best_news(ticker) if ticker else (None, [])

        sentiment = get_twitter_sentiment(titles)

        if best_news is None:
            news_text = "Aucune news dominante."
        else:
            news_text = best_news

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": """Tu es un trader professionnel.

Tu dois expliquer un mouvement de marché.

Règles :
- Utiliser la news dominante si elle existe
- Sinon utiliser le sentiment (Twitter)
- Sinon expliquer que c’est du momentum
- Ne jamais inventer
- Répondre comme un trader réel
"""
                },
                {
                    "role": "user",
                    "content": f"""
Question: {question}

News dominante:
{news_text}

Sentiment:
{sentiment}
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
