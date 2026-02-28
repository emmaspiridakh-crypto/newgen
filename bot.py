print(">>> BOT FILE LOADED <<<")
import os
import discord
import asyncio
import json
import time
from discord.ext import commands
from discord import app_commands

# ========================
# CONFIG
# ========================

TOKEN = os.getenv("TOKEN")

# ========================
# INTENTS & BOT
# ========================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

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

# LOG CHANNELS
LOG_CHANNEL_ID = 1474026151004340336
MESSAGE_EDIT_LOG_CHANNEL_ID = 1475520124894052465
MESSAGE_DELETE_LOG_CHANNEL_ID = 1475520124894052465
MEMBER_JOIN_LOG_CHANNEL_ID = 1475519852163895552
MEMBER_LEAVE_LOG_CHANNEL_ID = 1475519852163895552
ROLE_UPDATE_LOG_CHANNEL_ID = 1475520225792364716
VOICE_LOG_CHANNEL_ID = 1475520000461766726
CHANNEL_CREATE_LOG_CHANNEL_ID = 1475526632193396796
CHANNEL_DELETE_LOG_CHANNEL_ID = 1475526632193396796
ROLE_CREATE_LOG_CHANNEL_ID = 1475520225792364716
ROLE_DELETE_LOG_CHANNEL_ID = 1475520225792364716

# ========================
# HELPERS
# ========================

def is_owner_or_coowner(user: discord.Member):
    return any(r.id in (OWNER_ID, CO_OWNER_ID) for r in user.roles)

# ========================
# DUTY SYSTEM STORAGE
# ========================

DUTY_FILE = "duty.json"

def load_duty_data():
    if not os.path.exists(DUTY_FILE):
        with open(DUTY_FILE, "w") as f:
            json.dump({}, f)
    with open(DUTY_FILE, "r") as f:
        return json.load(f)

def save_duty_data(data):
    with open(DUTY_FILE, "w") as f:
        json.dump(data, f, indent=4)

duty_data = load_duty_data()

# ========================
# LOGGING EVENTS
# ========================

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if before.content == after.content:
        return

    channel = bot.get_channel(MESSAGE_EDIT_LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange()
        )
        embed.add_field(name="User", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content or "None", inline=False)
        embed.add_field(name="After", value=after.content or "None", inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    channel = bot.get_channel(MESSAGE_DELETE_LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=message.content or "None", inline=False)
        await channel.send(embed=embed)

# ========================
# VOICE LOGS
# ========================

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # TEMP VOICE SYSTEM
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

    if before.channel and before.channel.category_id == TEMP_VOICE_CATEGORY_ID:
        if before.channel.id != TEMP_VOICE_CHANNEL_ID:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                except:
                    pass

    # VOICE LOGGING
    if before.channel == after.channel:
        return

    channel = bot.get_channel(VOICE_LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎧 Voice Activity",
            color=discord.Color.purple()
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Before", value=str(before.channel), inline=False)
        embed.add_field(name="After", value=str(after.channel), inline=False)
        await channel.send(embed=embed)


# ========================
# CHANNEL CREATE / DELETE
# ========================

@bot.event
async def on_guild_channel_create(channel):
    log = bot.get_channel(CHANNEL_CREATE_LOG_CHANNEL_ID)
    if log:
        embed = discord.Embed(
            title="📁 Channel Created",
            color=discord.Color.green()
        )
        embed.add_field(name="Name", value=channel.name, inline=False)
        embed.add_field(name="Type", value=str(channel.type), inline=False)
        await log.send(embed=embed)


@bot.event
async def on_guild_channel_delete(channel):
    log = bot.get_channel(CHANNEL_DELETE_LOG_CHANNEL_ID)
    if log:
        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            color=discord.Color.red()
        )
        embed.add_field(name="Name", value=channel.name, inline=False)
        embed.add_field(name="Type", value=str(channel.type), inline=False)
        await log.send(embed=embed)


# ========================
# ROLE CREATE / DELETE
# ========================

@bot.event
async def on_guild_role_create(role):
    log = bot.get_channel(ROLE_CREATE_LOG_CHANNEL_ID)
    if log:
        embed = discord.Embed(
            title="🎨 Role Created",
            color=discord.Color.green()
        )
        embed.add_field(name="Role", value=role.mention, inline=False)
        await log.send(embed=embed)


@bot.event
async def on_guild_role_delete(role):
    log = bot.get_channel(ROLE_DELETE_LOG_CHANNEL_ID)
    if log:
        embed = discord.Embed(
            title="🗑️ Role Deleted",
            color=discord.Color.red()
        )
        embed.add_field(name="Role Name", value=role.name, inline=False)
        await log.send(embed=embed)


# ========================
# CLOSE BUTTON VIEW
# ========================

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        # LOG CLOSE
        if log_channel:
            embed = discord.Embed(
                title="❌ Ticket Closed",
                description=f"Το ticket έκλεισε από {interaction.user.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
            await log_channel.send(embed=embed)

        await interaction.response.send_message(
            "Το ticket θα κλείσει σε 2 δευτερόλεπτα...", ephemeral=False
        )

        await asyncio.sleep(2)

        try:
            await interaction.channel.delete(reason="Ticket closed")
        except:
            pass

# ============================
# SUPPORT TICKET PANEL
# ============================

class MainTicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Owner", description="Επικοινωνία με Owners / Co-Owners", emoji="👑"),
            discord.SelectOption(label="Bug", description="Αναφορά bug", emoji="🪲"),
            discord.SelectOption(label="Report", description="Αναφορά παίκτη / συμβάντος", emoji="📙"),
            discord.SelectOption(label="Support", description="Γενικό support", emoji="📩"),
        ]
        super().__init__(
            placeholder="Επίλεξε κατηγορία ticket...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        category = guild.get_channel(MAIN_TICKET_CATEGORY_ID)
        if not category:
            return await interaction.response.send_message("Η κατηγορία ticket δεν βρέθηκε.", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        if self.values[0] == "Owner":
            roles_ids = [OWNER_ID, CO_OWNER_ID]
            name = f"owner-{author.name}".replace(" ", "-").lower()
            ticket_type = "Owner Ticket"

        elif self.values[0] == "Bug":
            roles_ids = [DEVELOPER_ID, OWNER_ID, CO_OWNER_ID]
            name = f"bug-{author.name}".replace(" ", "-").lower()
            ticket_type = "Bug Report"

        elif self.values[0] == "Report":
            roles_ids = [ORGANIZER_ID, OWNER_ID, CO_OWNER_ID]
            name = f"report-{author.name}".replace(" ", "-").lower()
            ticket_type = "Report"

        else:
            roles_ids = [STAFF_ID, OWNER_ID, CO_OWNER_ID]
            name = f"support-{author.name}".replace(" ", "-").lower()
            ticket_type = "Support Ticket"

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
            reason=f"Ticket created by {author} ({ticket_type})"
        )

        embed = discord.Embed(
            title=f"🎫 Ticket από {author.name}",
            description=f"{author.mention} άνοιξε **{ticket_type}**.\n"
                        f"Παρακαλώ περιμένετε να σας εξυπηρετήσει ένα staff.",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketCloseView())

        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📂 Νέο Ticket",
                description=f"Ο χρήστης {author.mention} άνοιξε ticket.",
                color=discord.Color.blue()
            )
            log_embed.add_field(name="Τύπος", value=ticket_type)
            log_embed.add_field(name="Channel", value=channel.mention)
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message(
            f"Το ticket σου δημιουργήθηκε: {channel.mention}",
            ephemeral=True
        )


class MainTicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MainTicketSelect())


# ============================
# JOB TICKET PANEL
# ============================

class JobTicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Civilian Job", description="Civilian job", emoji="👮"),
            discord.SelectOption(label="Criminal Job", description="Criminal job", emoji="🕵️"),
        ]
        super().__init__(
            placeholder="Επιλέξτε job category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        category = guild.get_channel(JOB_TICKET_CATEGORY_ID)
        if not category:
            return await interaction.response.send_message("Η job ticket κατηγορία δεν βρέθηκε.", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        if self.values[0] == "Civilian Job":
            roles_ids = [CIVILIAN_ORG_ID]
            name = f"civilian-{author.name}".replace(" ", "-").lower()
            ticket_type = "Civilian Job"
        else:
            roles_ids = [CRIMINAL_ORG_ID]
            name = f"criminal-{author.name}".replace(" ", "-").lower()
            ticket_type = "Criminal Job"

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
            reason=f"Job ticket created by {author} ({ticket_type})"
        )

        embed = discord.Embed(
            title=f"🎫 Ticket από {author.name}",
            description=f"{author.mention} άνοιξε **{ticket_type}**.\n"
                        f"Παρακαλώ περιμένετε να σας εξυπηρετήσει ένας Organizer.",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketCloseView())

        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📂 Νέο Ticket",
                description=f"Ο χρήστης {author.mention} άνοιξε ticket.",
                color=discord.Color.blue()
            )
            log_embed.add_field(name="Τύπος", value=ticket_type)
            log_embed.add_field(name="Channel", value=channel.mention)
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message(
            f"Το job ticket σου δημιουργήθηκε: {channel.mention}",
            ephemeral=True
        )


class JobTicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(JobTicketSelect())

# ============================
# ON-DUTY SYSTEM (STAFF + DEVELOPERS)
# ============================

# ΒΑΛΕ ΕΔΩ ΤΑ ROLE IDs
STAFF_DUTY_ROLE_ID = 1476603226462748693  # Staff Duty Role
DEV_DUTY_ROLE_ID = 1476603396990701629    # Developer Duty Role


# ============================
# STAFF DUTY PANEL
# ============================

class StaffDutyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="On Duty", style=discord.ButtonStyle.green)
    async def staff_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(STAFF_DUTY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("❌ Ο ρόλος Staff Duty δεν βρέθηκε.", ephemeral=True)

        member = interaction.user

        if role in member.roles:
            return await interaction.response.send_message("Είσαι ήδη **On Duty**.", ephemeral=True)

        await member.add_roles(role)

        # Start tracking time
        duty_data[str(member.id)] = duty_data.get(str(member.id), {"hours": 0, "start": None})
        duty_data[str(member.id)]["start"] = time.time()
        save_duty_data(duty_data)

        await interaction.response.send_message("🟩 Μπήκες **On Duty**.", ephemeral=True)

    @discord.ui.button(label="Off Duty", style=discord.ButtonStyle.red)
    async def staff_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(STAFF_DUTY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("❌ Ο ρόλος Staff Duty δεν βρέθηκε.", ephemeral=True)

        member = interaction.user

        if role not in member.roles:
            return await interaction.response.send_message("Δεν είσαι **On Duty**.", ephemeral=True)

        await member.remove_roles(role)

        # Calculate hours
        entry = duty_data.get(str(member.id))
        if entry and entry["start"]:
            elapsed = (time.time() - entry["start"]) / 3600
            entry["hours"] += elapsed
            entry["start"] = None
            save_duty_data(duty_data)

        await interaction.response.send_message("🟥 Βγήκες **Off Duty**.", ephemeral=True)

    @discord.ui.button(label="Duty Stats", style=discord.ButtonStyle.blurple)
    async def staff_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📊 Staff Duty Stats",
            color=discord.Color.blurple()
        )

        for uid, info in duty_data.items():
            member = interaction.guild.get_member(int(uid))
            if not member:
                continue

            hours = info["hours"]
            if info["start"]:
                hours += (time.time() - info["start"]) / 3600

            embed.add_field(
                name=member.name,
                value=f"{hours:.2f} ώρες",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================
# DEVELOPER DUTY PANEL
# ============================

class DevWorkingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Working", style=discord.ButtonStyle.green)
    async def dev_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(DEV_DUTY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("❌ Ο ρόλος Developer Working δεν βρέθηκε.", ephemeral=True)

        member = interaction.user

        if role in member.roles:
            return await interaction.response.send_message("Είσαι ήδη **Working**.", ephemeral=True)

        await member.add_roles(role)

        duty_data[str(member.id)] = duty_data.get(str(member.id), {"hours": 0, "start": None})
        duty_data[str(member.id)]["start"] = time.time()
        save_duty_data(duty_data)

        await interaction.response.send_message("🟦 Μπήκες **Working** (Developer).", ephemeral=True)

    @discord.ui.button(label="Off Working", style=discord.ButtonStyle.red)
    async def dev_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(DEV_DUTY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("❌ Ο ρόλος Developer Working δεν βρέθηκε.", ephemeral=True)

        member = interaction.user

        if role not in member.roles:
            return await interaction.response.send_message("Δεν είσαι **Working**.", ephemeral=True)

        await member.remove_roles(role)

        entry = duty_data.get(str(member.id))
        if entry and entry["start"]:
            elapsed = (time.time() - entry["start"]) / 3600
            entry["hours"] += elapsed
            entry["start"] = None
            save_duty_data(duty_data)

        await interaction.response.send_message("🟥 Βγήκες **Off Working** (Developer).", ephemeral=True)

    @discord.ui.button(label="Work Stats", style=discord.ButtonStyle.blurple)
    async def dev_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📊 Developer Work Stats",
            color=discord.Color.blurple()
        )

        for uid, info in duty_data.items():
            member = interaction.guild.get_member(int(uid))
            if not member:
                continue

            hours = info["hours"]
            if info["start"]:
                hours += (time.time() - info["start"]) / 3600

            embed.add_field(
                name=member.name,
                value=f"{hours:.2f} ώρες",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

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


# ========================
# SUPPORT PANEL COMMAND
# ========================

@bot.command()
async def ticketpanel(ctx):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα να στείλεις το panel.")

    embed = discord.Embed(
        title="🎫 Welcome to Paradox King Remastered",
        description=(
            "Για άμεση εξυπηρέτηση, επίλεξε την κατηγορία που ταιριάζει στο αίτημά σου.\n"
            "Η ομάδα μας θα σε εξυπηρετήσει το συντομότερο δυνατό."
        ),
        color=0x2b2d31
    )

    embed.set_image(url="https://cdn.discordapp.com/attachments/1392390677648893236/1392396770040324176/Jgt5WZxlUs17dbWZv0eZ1.jpeg")
    embed.set_footer(text="Paradox King Remastered • Support System")

    await ctx.send(embed=embed, view=MainTicketPanel())
    await ctx.reply("Το νέο ticket panel στάλθηκε.", delete_after=2)


# ========================
# JOB PANEL COMMAND
# ========================

@bot.command()
async def jobpanel(ctx):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα να στείλεις το panel.")

    embed = discord.Embed(
        title="📋 Paradox King Remastered — Job Tickets",
        description=(
            "Επέλεξε την κατηγορία job που ταιριάζει στο αίτημά σου.\n"
            "Η ομάδα μας θα σε εξυπηρετήσει άμεσα."
        ),
        color=0x2b2d31
    )

    embed.set_image(url="https://cdn.discordapp.com/attachments/1392390677648893236/1392396770040324176/Jgt5WZxlUs17dbWZv0eZ1.jpeg")
    embed.set_footer(text="Paradox King Remastered • Job Support")

    await ctx.send(embed=embed, view=JobTicketPanel())
    await ctx.reply("Το νέο job ticket panel στάλθηκε.", delete_after=2)


# ========================
# WHITELIST PANEL COMMAND
# ========================

@bot.command()
async def whitelistpanel(ctx):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα να στείλεις το panel.")

    embed = discord.Embed(
        title="📋 Whitelist Application",
        description="Πάτησε το κουμπί για να κάνεις αίτηση whitelist.",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed, view=WhitelistApplyButton())
    await ctx.reply("Το whitelist panel στάλθηκε.", delete_after=2)


# ========================
# STAFF DUTY PANEL COMMAND
# ========================

@bot.command()
async def staffduty(ctx):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα.")

    embed = discord.Embed(
        title="🟩 Staff On-Off-Duty Panel",
        description="Πάτησε ένα κουμπί:",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed, view=StaffDutyView())
    await ctx.reply("Το Staff Duty Panel στάλθηκε.", delete_after=2)


# ========================
# DEVELOPER DUTY PANEL COMMAND
# ========================

@bot.command()
async def devduty(ctx):
    if not is_owner_or_coowner(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα.")

    embed = discord.Embed(
        title="🟦 Developer On-Off-Work Panel",
        description="Πάτησε ένα κουμπί:",
        color=discord.Color.yellow()
    )

    await ctx.send(embed=embed, view=DevDutyView())
    await ctx.reply("Το Developer Working Panel στάλθηκε.", delete_after=2)


# ================================
# EVENTS
# ================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ================================
# START BOT
# ================================

if __name__ == "__main__":
    bot.run(TOKEN)


















