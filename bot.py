import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Config
with open("config.json") as f:
    config = json.load(f)

# Logging su file
def log_action(action, moderator, target, reason):
    if not os.path.exists("logs"):
        os.makedirs("logs")
    with open("logs/moderation.log", "a") as f:
        f.write(f"[{datetime.now()}] {action} | {moderator} -> {target} | Motivo: {reason}\n")

# Logging su canale Discord
async def send_log_embed(guild, embed):
    log_channel = discord.utils.get(guild.text_channels, name="mod-log")
    if log_channel:
        await log_channel.send(embed=embed)

# Evento on_ready
@bot.event
async def on_ready():
    print(f"Bot online come {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Slash commands sincronizzati: {len(synced)}")
    except Exception as e:
        print(e)

# BAN
@tree.command(name="ban", description="Banna un utente")
@app_commands.describe(user="Utente da bannare", reason="Motivo del ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Nessun motivo"):
    await user.ban(reason=reason)
    embed = discord.Embed(title="Utente Bannato", description=f"{user.mention} è stato bannato", color=discord.Color.red())
    embed.add_field(name="Motivo", value=reason)
    embed.set_footer(text=f"Bannato da {interaction.user}")
    await interaction.response.send_message(embed=embed)
    await send_log_embed(interaction.guild, embed)
    log_action("BAN", interaction.user, user, reason)

# KICK
@tree.command(name="kick", description="Espelli un utente")
@app_commands.describe(user="Utente da espellere", reason="Motivo del kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Nessun motivo"):
    await user.kick(reason=reason)
    embed = discord.Embed(title="Utente Espulso", description=f"{user.mention} è stato espulso", color=discord.Color.orange())
    embed.add_field(name="Motivo", value=reason)
    embed.set_footer(text=f"Espulso da {interaction.user}")
    await interaction.response.send_message(embed=embed)
    await send_log_embed(interaction.guild, embed)
    log_action("KICK", interaction.user, user, reason)

# WARN
@tree.command(name="warn", description="Avvisa un utente")
@app_commands.describe(user="Utente da avvisare", reason="Motivo dell'avvertimento")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "Comportamento scorretto"):
    embed = discord.Embed(title="Avvertimento", description=f"{user.mention} ha ricevuto un avvertimento", color=discord.Color.yellow())
    embed.add_field(name="Motivo", value=reason)
    embed.set_footer(text=f"Avvertito da {interaction.user}")
    await interaction.response.send_message(embed=embed)
    await send_log_embed(interaction.guild, embed)
    log_action("WARN", interaction.user, user, reason)

# MUTE
@tree.command(name="mute", description="Muta un utente per X minuti")
@app_commands.describe(user="Utente da mutare", minutes="Durata del mute", reason="Motivo")
async def mute(interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "Mute temporaneo"):
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(mute_role, send_messages=False, speak=False)

    await user.add_roles(mute_role, reason=reason)
    embed = discord.Embed(title="Utente Mutato", description=f"{user.mention} è stato mutato per {minutes} minuti", color=discord.Color.dark_gray())
    embed.add_field(name="Motivo", value=reason)
    embed.set_footer(text=f"Mutato da {interaction.user}")
    await interaction.response.send_message(embed=embed)
    await send_log_embed(interaction.guild, embed)
    log_action("MUTE", interaction.user, user, f"{reason} ({minutes} min)")

    await asyncio.sleep(minutes * 60)
    await user.remove_roles(mute_role)

# STATS
@tree.command(name="stats", description="Mostra le statistiche di moderazione")
async def stats(interaction: discord.Interaction):
    if not os.path.exists("logs/moderation.log"):
        await interaction.response.send_message("Nessuna azione registrata.")
        return

    with open("logs/moderation.log", "r") as f:
        lines = f.readlines()

    actions = {"BAN": 0, "KICK": 0, "MUTE": 0, "WARN": 0}
    for line in lines:
        for key in actions:
            if key in line:
                actions[key] += 1

    embed = discord.Embed(title="Statistiche Moderazione", color=discord.Color.blue())
    for action, count in actions.items():
        embed.add_field(name=action, value=str(count), inline=True)

    await interaction.response.send_message(embed=embed)

# Avvio bot
bot.run(config["token"])
