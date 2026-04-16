import discord
import os
from openai import OpenAI

# 🔐 Secrets (GitHub)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🤖 Client OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ⚙️ Discord setup
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# 🎯 Personnalité TEA
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
    # ❌ Ignore ses propres messages
    if message.author == bot.user:
        return

    # 🎯 Commande principale
    if message.content.startswith("!tea"):
        question = message.content.replace("!tea", "").strip()

        if question == "":
            await message.channel.send("Pose une question après !tea")
            return

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",  # modèle stable
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question}
                ]
            )

            # 🔥 Extraction propre de la réponse
            reply = response.output_text

            # 🔒 Sécurité limite Discord (2000 caractères)
            if not reply:
                reply = "Je n'ai pas pu générer de réponse."

            reply = reply[:1900]

            await message.channel.send(reply)

        except Exception as e:
            print("ERREUR OPENAI:", e)
            await message.channel.send("Erreur, réessaie.")

# 🚀 Lancement
bot.run(DISCORD_TOKEN)
