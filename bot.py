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
Tu es un trader professionnel expérimenté.

Style:
- Direct
- Sans bullshit
- Réponses courtes (3-6 lignes)
- Tu penses en probabilités

Tu aides les utilisateurs à comprendre les marchés.
Tu ne promets jamais de gains.
"""

@bot.event
async def on_ready():
    print(f"Connecté comme {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!tea"):
        question = message.content.replace("!tea", "").strip()

        if question == "":
            await message.channel.send("Pose une vraie question après !tea")
            return

        try:
            response = client.responses.create(
                model="gpt-5.3",
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question}
                ]
            )

            reply = response.output_text
            await message.channel.send(reply)

        except Exception as e:
            await message.channel.send("Erreur, réessaie.")
            print(e)

bot.run(DISCORD_TOKEN)
