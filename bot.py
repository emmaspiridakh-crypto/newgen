import os
import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread

# ========================
# CONFIG
# ========================

TOKEN = "MTQ2OTY4NzY0MDQxNTUzOTI2NQ.GmOkWS.PK9jfTgC_LRlMT-7RaVS7hdXGwJS8XaryFqgjI"
GUILD_ID = 1469054622550462720

# ROLE IDs
OWNER_ID = 1469054622965567594
CO_OWNER_ID = 1469054622965567593
DEVELOPER_ID = 1469054622957305897
ORGANIZER_ID = 1469054622957305906
STAFF_ID = 1469054622919295216
CIVILIAN_ORG_ID = 1469054622957305900
CRIMINAL_ORG_ID = 1469054622957305899

# CATEGORY IDs
MAIN_TICKET_CATEGORY_ID = 1469054624077189183
JOB_TICKET_CATEGORY_ID = 1469698048686030931

# AUTOROLE
AUTOROLE_ID = 1469054622906847473

# TEMP VOICE
TEMP_VOICE_CATEGORY_ID = 1469054624077189184
TEMP_VOICE_CHANNEL_ID = 1469054624077189187

# ========================
# INTENTS & BOT
# ========================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# ========================
# AUTOROLE
# ========================

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(AUTOROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass


# ========================
# TEMP VOICE
# ========================

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # Join-to-create
    if after.channel and after.channel.id == TEMP_VOICE_CHANNEL_ID:
        category = guild.get_channel(TEMP_VOICE_CATEGORY_ID)

        temp_channel = await guild.create_voice_channel(
            name=f"{member.name}'s Channel",
            category=category
        )

        try:
            await member.move_to(temp_channel)
        except:
            pass

    # Delete empty temp channels
    if before.channel and before.channel.category_id == TEMP_VOICE_CATEGORY_ID:
        if before.channel.id != TEMP_VOICE_CHANNEL_ID:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                except:
                    pass


# ========================
# KEEP ALIVE (Render + UptimeRobot)
# ========================

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# ========================
# HELPERS
# ========================

def is_owner_or_coowner(user: discord.Member):
    return any(r.id in (OWNER_ID, CO_OWNER_ID) for r in user.roles)


# ========================
# CLOSE BUTTON VIEW
# ========================

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Το ticket θα κλείσει σε 5 δευτερόλεπτα...", ephemeral=True
        )
       await asyncio.sleep(5)
       try:   
            await interaction.channel.delete(reason="Ticket closed")
        except:
            pass


# ============================
# PANEL 1 - Owners / Bug / Report / Support
# ============================

class MainTicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Owner", description="Επικοινωνία με Owners / Co-Owners", emoji="👑"),
            discord.SelectOption(label="Bug", description="Αναφορά bug", emoji="🪲"),
            discord.SelectOption(label="Report", description="Αναφορά παίκτη / συμβάντος", emoji="📙"),
            discord.SelectOption(label="Support", description="Γενικό support", emoji="📩"),
        ]
        super().__init__(placeholder="Επίλεξε κατηγορία ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        category = guild.get_channel(MAIN_TICKET_CATEGORY_ID)

        if category is None or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("Η κατηγορία ticket δεν βρέθηκε.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        if self.values[0] == "Owner":
            roles_ids = [OWNER_ID, CO_OWNER_ID]
            name = f"owner-{author.name}"
        elif self.values[0] == "Bug":
            roles_ids = [DEVELOPER_ID, OWNER_ID, CO_OWNER_ID]
            name = f"bug-{author.name}"
        elif self.values[0] == "Report":
            roles_ids = [ORGANIZER_ID, OWNER_ID, CO_OWNER_ID]
            name = f"report-{author.name}"
        else:
            roles_ids = [STAFF_ID, OWNER_ID, CO_OWNER_ID]
            name = f"support-{author.name}"

        for rid in roles_ids:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {author} ({self.values[0]})"
        )

        await channel.send(
            content=f"{author.mention} το ticket σου δημιουργήθηκε.",
            view=TicketCloseView()
        )

        await interaction.response.send_message(
            f"Το ticket σου δημιουργήθηκε: {channel.mention}", ephemeral=True
        )


class MainTicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MainTicketSelect())


# ========================
# PANEL 2 - Civilian Job / Criminal Job
# ========================

class JobTicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Civilian Job", description="Civilian job", emoji="👮"),
            discord.SelectOption(label="Criminal Job", description="Criminal job", emoji="🕵️"),
        ]
        super().__init__(placeholder="Επιλέξτε job category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        category = guild.get_channel(JOB_TICKET_CATEGORY_ID)

        if category is None or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("Η job ticket κατηγορία δεν βρέθηκε.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        if self.values[0] == "Civilian Job":
            roles_ids = [CIVILIAN_ORG_ID]
            name = f"civilian-{author.name}"
        else:
            roles_ids = [CRIMINAL_ORG_ID]
            name = f"criminal-{author.name}"

        for rid in roles_ids:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites,
            reason=f"Job ticket created by {author} ({self.values[0]})"
        )

        await channel.send(
            content=f"{author.mention} το job ticket σου δημιουργήθηκε.",
            view=TicketCloseView()
        )

        await interaction.response.send_message(
            f"Το job ticket σου δημιουργήθηκε: {channel.mention}", ephemeral=True
        )


class JobTicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(JobTicketSelect())


# ========================
# COMMANDS
# ========================

@bot.command()
async def say(ctx, *, message: str):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα να χρησιμοποιήσεις αυτή την εντολή.")
    await ctx.send(message)


@bot.command()
async def dmall(ctx, *, message: str):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα να χρησιμοποιήσεις αυτή την εντολή.")
    sent = 0
    for member in ctx.guild.members:
        if member.bot:
            continue
        try:
            await member.send(message)
            sent += 1
        except:
            continue
    await ctx.reply(f"Το μήνυμα στάλθηκε σε {sent} μέλη.")


@bot.command()
async def ticketpanel(ctx):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα να στείλεις το panel.")
    embed = discord.Embed(
        title="🎫 Tickets",
        description="Επέλεξε την κατηγορία που θέλεις να ανοίξεις ticket.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=MainTicketPanel())
    await ctx.reply("Το main ticket panel στάλθηκε.", delete_after=2)


@bot.command()
async def jobpanel(ctx):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα να στείλεις το panel.")
    embed = discord.Embed(
        title="📋 Job Tickets",
        description="Επέλεξε job category που θέλεις.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=JobTicketPanel())
    await ctx.reply("Το job ticket panel στάλθηκε.", delete_after=2)


# ================================
# EVENTS
# ================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print("Slash sync error:", e)


# ================================
# START
# ================================

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)



