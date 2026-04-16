import discord
import os
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Connecté comme {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!tea"):
        question = message.content.replace("!tea", "").strip()

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",  # 🔥 modèle stable pour test
                input=question
            )

            print("REPONSE OPENAI:", response)

            await message.channel.send(str(response))

        except Exception as e:
            print("ERREUR OPENAI COMPLETE:", e)
            await message.channel.send(f"Erreur: {e}")

bot.run(DISCORD_TOKEN)
