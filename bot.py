import discord
import os
from openai import OpenAI

# 🔐 Secrets GitHub
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ⚙️ Discord setup
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
SYSTEM_PROMPT = """
Tu es un trader professionnel spécialisé uniquement dans les marchés financiers.

RÈGLE ABSOLUE:
- Tu réponds UNIQUEMENT en contexte trading / bourse / finance.
- Si une question peut avoir plusieurs significations, tu DOIS prendre la version financière.
- Tu ignores totalement les autres significations (santé, administratif, etc.).
- Tu n’énumères JAMAIS d’autres définitions.

SI CE N’EST PAS FINANCIER:
Tu réponds: "Je réponds uniquement aux questions liées aux marchés financiers."

Style:
- Direct
- Sans bullshit
- Réponses courtes (3-6 lignes)
- Approche probabiliste

Tu es un trader, pas un encyclopédie.
"""

@bot.event
async def on_ready():
    print(f"Connecté comme {bot.user}")

@bot.event
async def on_message(message):
    # ❌ ignore les messages du bot
    if message.author == bot.user:
        return

    # ======================
    # 🔹 COMMANDE !tea
    # ======================
    if message.content.startswith("!tea"):
        question = message.content.replace("!tea", "").strip()

        if question == "":
            await message.channel.send("Pose une question après !tea")
            return

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=question
            )

            # 🔥 extraction propre (ULTRA IMPORTANT)
            reply = ""

            if hasattr(response, "output") and response.output:
                for item in response.output:
                    if hasattr(item, "content"):
                        for c in item.content:
                            if hasattr(c, "text"):
                                reply += c.text

            # fallback
            if reply == "":
                reply = "Je n'ai pas pu générer une réponse."

            # 🔒 sécurité Discord
            reply = reply[:1900]

            await message.channel.send(reply)

        except Exception as e:
            print("ERREUR OPENAI:", e)
            await message.channel.send("Erreur, réessaie.")

# 🚀 lancement
bot.run(DISCORD_TOKEN)
