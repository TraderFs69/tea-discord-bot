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

    if message.author == bot.user:
        return

    await message.channel.send("Je fonctionne")

bot.run(DISCORD_TOKEN)
