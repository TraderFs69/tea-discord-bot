import discord
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"BOT CONNECTÉ: {bot.user}")

@bot.event
async def on_message(message):
    print("MESSAGE REÇU:", message.content)

    # Ignore les messages du bot
    if message.author == bot.user:
        return

    # Commande test
    if message.content == "!test":
        await message.channel.send("Bot OK")
        return

    # Commande analyse (simple pour tester)
    if message.content.startswith("!analyse"):
        ticker = message.content.replace("!analyse", "").strip().upper()

        if ticker == "":
            await message.channel.send("Ex: !analyse TSLA")
            return

        await message.channel.send(f"Analyse reçue pour {ticker}")
        return

bot.run(DISCORD_TOKEN)
