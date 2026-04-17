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
# 📊 DATA POLYGON
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

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df

# ======================
# 🧠 SCORING SYSTEM
# ======================
def score_stock(df):
    last = df.iloc[-1]

    score = 0

    # Trend
    if last["close"] > last["ema50"]:
        score += 25
    if last["ema9"] > last["ema20"]:
        score += 25

    # Momentum
    if last["rsi"] > 50:
        score += 25

    # Strength
    if last["close"] > last["ema20"]:
        score += 25

    return score

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

    # ======================
    # 🔹 ANALYSE PRO
    # ======================
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
        last = df.iloc[-1]

        # 🔥 INTERPRÉTATION
        if score >= 75:
            bias = "Bullish fort"
        elif score >= 50:
            bias = "Bullish modéré"
        elif score >= 25:
            bias = "Neutre / faible"
        else:
            bias = "Bearish"

        prompt = f"""
Tu es un trader hedge fund.

Données:
Prix: {last['close']:.2f}
RSI: {last['rsi']:.2f}
EMA9: {last['ema9']:.2f}
EMA20: {last['ema20']:.2f}
EMA50: {last['ema50']:.2f}
Score: {score}/100
Biais: {bias}

Donne:
- lecture rapide
- scénario probable
- risque

Style desk, direct, sans bullshit.
"""

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt
            )

            reply = response.output_text or "Erreur analyse."
            reply = reply[:1900]

            await message.channel.send(f"📊 {ticker} | Score: {score}/100 | {bias}\n\n{reply}")

        except Exception as e:
            print(e)
            await message.channel.send("Erreur analyse.")

bot.run(DISCORD_TOKEN)
