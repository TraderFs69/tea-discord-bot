import discord
import os
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

SYSTEM_PROMPT = """
Tu es un trader professionnel.
Réponses courtes, directes, sans bullshit.
Tu penses en probabilités.
"""

@bot.event
async def on_ready():
    print(f"Connecté comme {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!tea"):
        question = message.content.replace("!tea", "")

        response = client.responses.create(
            model="gpt-5.3",
            input=question
        )

        await message.channel.send(response.output_text)

bot.run(DISCORD_TOKEN)
