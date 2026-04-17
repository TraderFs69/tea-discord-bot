import discord
import os
import requests
import pandas as pd
import numpy as np
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
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/200?adjusted=true&apiKey={POLYGON_API_KEY}"
    r = requests.get(url)
    data = r.json()

    if "results" not in data:
        return None

    df = pd.DataFrame(data["results"])
    df["close"] = df["c"]
    return df

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
# 🧠 SCORING
# ======================
def score_stock(df):
    last = df.iloc[-1]

    score = 0

    # Trend
    if last["close"] > last["ema50"]:
        score += 30

    # Structure
    if last["ema9"] > last["ema20"]:
        score += 25

    # Momentum
    if last["rsi"] > 50:
        score += 20

    # Strength
    if last["close"] > last["ema20"]:
        score += 25

    return score

# ======================
# 📊 ANALYSE STRUCTURÉE
# ======================
def build_analysis(df, score):
    last = df.iloc[-1]

    # Bias
    if score >= 75:
        bias = "Bullish fort"
    elif score >= 50:
        bias = "Bullish modéré"
    elif score >= 30:
        bias = "Neutre"
    else:
        bias = "Bearish"

    # Structure logique (PAS IA)
    if last["close"] > last["ema20"]:
        structure = "au-dessus EMA20 (structure haussière)"
    else:
        structure = "sous EMA20 (structure fragile)"

    # Momentum logique
    if last["rsi"] > 60:
        momentum = "fort"
    elif last["rsi"] > 50:
        momentum = "positif"
    else:
        momentum = "faible"

    # Scénario logique
    if score >= 60:
        scenario = "continuation haussière probable"
    elif score >= 40:
        scenario = "range / consolidation"
    else:
        scenario = "pression baissière probable"

    # Risque logique
    risk = "perte EMA20 = affaiblissement"

    return {
        "bias": bias,
        "structure": structure,
        "momentum": momentum,
        "scenario": scenario,
        "risk": risk,
        "price": last["close"],
        "rsi": last["rsi"]
    }

# ======================
# 🤖 BOT
# ======================
@bot.event
async def on_ready():
    print(f"Connecté comme {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!analyse"):
        ticker = message.content.replace("!analyse", "").strip().upper()

        if ticker == "":
            await message.channel.send("Ex: !analyse TSLA")
            return

        df = get_data(ticker)

        if df is None:
            await message.channel.send("Erreur données.")
            return

        df = calculate_indicators(df)
        score = score_stock(df)
        analysis = build_analysis(df, score)

        # 🔥 FORMAT FINAL (100% contrôlé)
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

bot.run(DISCORD_TOKEN)
