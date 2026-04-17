import discord
import os
import requests
import pandas as pd
from openai import OpenAI

# 🔐 KEYS
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ======================
# 📊 DATA
# ======================
def get_data(ticker):
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/200?adjusted=true&apiKey={POLYGON_API_KEY}"
        r = requests.get(url)
        data = r.json()

        if "results" not in data:
            return None

        df = pd.DataFrame(data["results"])
        df["close"] = df["c"]
        return df

    except Exception as e:
        print("ERREUR DATA:", e)
        return None

# ======================
# 📈 INDICATORS
# ======================
def calculate_indicators(df):
    df["ema9"] = df["close"].ewm(span=9).mean()
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df

# ======================
# 🧠 SCORE
# ======================
def score_stock(df):
    last = df.iloc[-1]
    score = 0

    if last["close"] > last["ema50"]:
        score += 30
    if last["ema9"] > last["ema20"]:
        score += 25
    if last["rsi"] > 50:
        score += 20
    if last["close"] > last["ema20"]:
        score += 25

    return score

# ======================
# 📊 ANALYSE
# ======================
def build_analysis(df, score):
    last = df.iloc[-1]

    if score >= 75:
        bias = "Bullish fort"
    elif score >= 50:
        bias = "Bullish modéré"
    elif score >= 30:
        bias = "Neutre"
    else:
        bias = "Bearish"

    structure = "au-dessus EMA20" if last["close"] > last["ema20"] else "sous EMA20"
    momentum = "fort" if last["rsi"] > 60 else "positif" if last["rsi"] > 50 else "faible"

    scenario = (
        "continuation haussière probable"
        if score >= 60
        else "consolidation"
        if score >= 40
        else "pression baissière"
    )

    risk = "perte EMA20 = affaiblissement"

    return {
        "bias": bias,
        "structure": structure,
        "momentum": momentum,
        "scenario": scenario,
        "risk": risk,
        "price": last["close"],
        "rsi": last["rsi"],
    }

# ======================
# 🤖 BOT
# ======================
@bot.event
async def on_ready():
    print(f"Connecté comme {bot.user}")

@bot.event
async def on_message(message):
    print("MESSAGE REÇU:", message.content)  # 🔥 DEBUG

    if message.author == bot.user:
        return

    # ======================
    # 🔹 TEST SIMPLE
    # ======================
    if message.content == "!test":
        await message.channel.send("Bot OK")
        return

    # ======================
    # 🔹 ANALYSE
    # ======================
    if message.content.startswith("!analyse"):
        ticker = message.content.replace("!analyse", "").strip().upper()

        if ticker == "":
            await message.channel.send("Ex: !analyse TSLA")
            return

        await message.channel.send(f"Analyse en cours: {ticker}...")

        df = get_data(ticker)

        if df is None:
            await message.channel.send("Erreur récupération données.")
            return

        df = calculate_indicators(df)
        score = score_stock(df)
        analysis = build_analysis(df, score)

        reply = f"""
📊 {ticker} | Score: {score}/100 | {analysis['bias']}

Prix: {analysis['price']:.2f}
RSI: {analysis['rsi']:.1f}

Structure: {analysis['structure']}
Momentum: {analysis['momentum']}

Scénario: {analysis['scenario']}
Risque: {analysis['risk']}
"""

        await message.channel.send(reply[:1900])

# 🚀 RUN
bot.run(DISCORD_TOKEN)
