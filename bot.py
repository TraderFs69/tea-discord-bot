import discord
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print("BOT CONNECTÉ")

@bot.event
async def on_message(message):
    print("MESSAGE:", message.content)

    if message.author == bot.user:
        return

    if message.content == "!test":
        await message.channel.send("OK")
        return

    if message.content.startswith("!analyse"):
        await message.channel.send("Analyse OK")
        return

bot.run(DISCORD_TOKEN)
