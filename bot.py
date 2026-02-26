print(">>> BOT FILE LOADED <<<")
import os
import discord
import asyncio
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

# ANTI-ALT CONFIG
ALT_ALERT_CHANNEL_ID = 1475521422980939980
ALT_MIN_ACCOUNT_AGE_DAYS = 10
ALT_REQUIRE_PFP = True
ALT_SUSPICIOUS_NAME = True

# ========================
# HELPERS
# ========================

def is_owner_or_coowner(user: discord.Member):
    return any(r.id in (OWNER_ID, CO_OWNER_ID) for r in user.roles)

def has_whitelist_permission(member: discord.Member):
    role_ids = [OWNER_ID, CO_OWNER_ID, WHITELIST_MANAGER_ROLE_ID]
    return any(r.id in role_ids for r in member.roles)

# ========================
# LOGGING EVENTS (FIXED)
# ========================

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if before.type != discord.MessageType.default:
        return
    if hasattr(before, "interaction") and before.interaction is not None:
        return
    if not before.content and before.embeds:
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
    if message.type != discord.MessageType.default:
        return
    if hasattr(message, "interaction") and message.interaction is not None:
        return
    if not message.content and message.embeds:
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
# MEMBER JOIN / LEAVE
# ========================

@bot.event
async def on_member_join(member):
    # Autorole
    role = member.guild.get_role(AUTOROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

    # Logging
    channel = bot.get_channel(MEMBER_JOIN_LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="📥 Member Joined",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account Created", value=str(member.created_at), inline=False)
        await channel.send(embed=embed)

    # Anti-alt detection
    await anti_alt_check(member)


@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(MEMBER_LEAVE_LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="📤 Member Left",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        await channel.send(embed=embed)


# ========================
# ROLE UPDATES
# ========================

@bot.event
async def on_member_update(before, after):
    # Avoid duplicate triggers
    if before.roles == after.roles:
        return

    channel = bot.get_channel(ROLE_UPDATE_LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎭 Role Update",
            color=discord.Color.blue()
        )
        embed.add_field(name="User", value=f"{after} ({after.id})", inline=False)

        before_set = set(before.roles)
        after_set = set(after.roles)

        added = after_set - before_set
        removed = before_set - after_set

        if added:
            embed.add_field(name="Added Roles", value=", ".join([r.mention for r in added]), inline=False)
        if removed:
            embed.add_field(name="Removed Roles", value=", ".join([r.mention for r in removed]), inline=False)

        await channel.send(embed=embed)


# ========================
# VOICE LOGS (FIXED)
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

    # VOICE LOGGING (avoid duplicates)
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
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
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
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
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
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
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
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
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
            embed.add_field(name="Channel")
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
# PANEL 1 - Owners / Bug / Report / Support
# ============================

class MainTicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Owner", description="Επικοινωνία με Owners / Co-Owners", emoji="👑"),
            discord.SelectOption(label="Bug", description="Αναφορά bug", emoji="🪲"),
            discord.SelectOption(label="Report", description="Αναφορά παίκτη / συμβάντος", emoji="📙"),
            discord.SelectOption(label="Support", description="Γενικό support", emoji="📩"),
        ], timeout=None)
        super().__init__(placeholder="Επίλεξε κατηγορία ticket....", min_values=1, max_values=1, options=options)

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

        # Ticket type + roles + channel name
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

        # Add staff permissions
        for rid in roles_ids:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        # Create ticket channel
        channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {author} ({ticket_type})"
        )

        # EMBED MESSAGE INSIDE TICKET
        embed = discord.Embed(
            title=f"🎫 Ticket από {author.name}",
            description=f"{author.mention} άνοιξε **{ticket_type}**.\n"
                        f"Παρακαλώ περιμένετε να σας εξυπηρετήσει ένα staff.",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketCloseView())

        # LOG OPEN
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📂 Νέο Ticket",
                description=f"Ο χρήστης {author.mention} άνοιξε ticket.",
                color=discord.Color.blue()
            )
            log_embed.add_field(name="Τύπος", value=ticket_type)
            await log_channel.send(embed=log_embed)

        # USER RESPONSE
        await interaction.response.send_message(
            f"Το ticket σου δημιουργήθηκε: {channel.mention}",
            ephemeral=True
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

        # EMBED MESSAGE INSIDE TICKET
        embed = discord.Embed(
            title=f"🎫 Ticket από {author.name}",
            description=f"{author.mention} άνοιξε **{ticket_type}**.\n"
                        f"Παρακαλώ περιμένετε να σας εξυπηρετήσει ένας Organizer.",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketCloseView())

        # LOG OPEN
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📂 Νέο Ticket",
                description=f"Ο χρήστης {author.mention} άνοιξε ticket.",
                color=discord.Color.blue()
            )
            log_embed.add_field(name="Τύπος", value=ticket_type)
            await log_channel.send(embed=log_embed)

        # USER RESPONSE
        await interaction.response.send_message(
            f"Το job ticket σου δημιουργήθηκε: {channel.mention}",
            ephemeral=True
        )


class JobTicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(JobTicketSelect())

# ========================
# WHITELIST SYSTEM
# ========================

class WhitelistReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_whitelist_permission(interaction.user):
            return await interaction.response.send_message(
                "Δεν έχεις δικαίωμα να διαχειριστείς whitelist.", ephemeral=True
            )

        await interaction.response.send_message(
            "Γράψε το reason για **ACCEPT** σε ένα μήνυμα σε αυτό το κανάλι.", ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            return

        reason = msg.content
        await handle_whitelist_decision(interaction, approved=True, reason=reason)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_whitelist_permission(interaction.user):
            return await interaction.response.send_message(
                "Δεν έχεις δικαίωμα να διαχειριστείς whitelist.", ephemeral=True
            )

        await interaction.response.send_message(
            "Γράψε το reason για **DENY** σε ένα μήνυμα σε αυτό το κανάλι.", ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            return

        reason = msg.content
        await handle_whitelist_decision(interaction, approved=False, reason=reason)


async def handle_whitelist_decision(interaction: discord.Interaction, approved: bool, reason: str):
    guild = interaction.guild
    review_message = interaction.message
    data = whitelist_applications.get(review_message.id)

    if not data:
        return await interaction.followup.send("Δεν βρέθηκαν δεδομένα για αυτή την αίτηση.", ephemeral=True)

    user_id = data["user_id"]
    ticket_channel_id = data["ticket_channel_id"]

    member = guild.get_member(user_id)
    ticket_channel = guild.get_channel(ticket_channel_id)
    log_channel = guild.get_channel(WHITELIST_LOG_CHANNEL_ID) or guild.get_channel(LOG_CHANNEL_ID)

    # DM στον χρήστη
    if member:
        try:
            if approved:
                dm_text = f"✅ Η whitelist αίτησή σου **έγινε δεκτή** από {interaction.user.mention}.\nReason: {reason}"
            else:
                dm_text = f"❌ Η whitelist αίτησή σου **απορρίφθηκε** από {interaction.user.mention}.\nReason: {reason}"
            await member.send(dm_text)
        except:
            pass

    # Role add αν είναι approved
    if approved and member:
        wl_role = guild.get_role(WHITELISTED_ROLE_ID)
        if wl_role:
            try:
                await member.add_roles(wl_role, reason="Whitelist approved")
            except:
                pass

    # Logs
    if log_channel:
        status = "APPROVED" if approved else "DENIED"
        color = discord.Color.green() if approved else discord.Color.red()
        embed = discord.Embed(
            title=f"Whitelist {status}",
            color=color
        )
        if member:
            embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
        embed.add_field(name="Staff", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
        if ticket_channel:
            embed.add_field(name="Ticket Channel", value=ticket_channel.mention, inline=False)
        await log_channel.send(embed=embed)

    # Κλείσιμο ticket
    if ticket_channel:
        try:
            await ticket_channel.delete(reason="Whitelist application processed")
        except:
            pass

    # Ενημέρωση review message
    try:
        status_text = "✅ ACCEPTED" if approved else "❌ DENIED"
        new_embed = review_message.embeds[0] if review_message.embeds else discord.Embed()
        new_embed.add_field(name="Status", value=status_text, inline=False)
        new_embed.add_field(name="Handled by", value=interaction.user.mention, inline=False)
        await review_message.edit(embed=new_embed, view=None)
    except:
        pass

    await interaction.followup.send(
        f"Η αίτηση {'εγκρίθηκε' if approved else 'απορρίφθηκε'} επιτυχώς.", ephemeral=True
    )


class WhitelistApplyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for Whitelist", style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user
        now = asyncio.get_event_loop().time()

        # Cooldown check
        if user.id in whitelist_cooldown:
            remaining = whitelist_cooldown[user.id] - now
            if remaining > 0:
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return await interaction.response.send_message(
                    f"Μπορείς να ξανακάνεις αίτηση σε **{hours} ώρες και {minutes} λεπτά**.",
                    ephemeral=True
                )

        guild = interaction.guild
        category = guild.get_channel(MAIN_TICKET_CATEGORY_ID)

        if category is None or not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Η κατηγορία για whitelist applications δεν βρέθηκε.", ephemeral=True
            )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        channel = await guild.create_text_channel(
            name=f"application-{user.name}".replace(" ", "-").lower(),
            category=category,
            overwrites=overwrites,
            reason=f"Whitelist application by {user}"
        )

        # Αποθήκευση cooldown
        whitelist_cooldown[user.id] = now + WHITELIST_COOLDOWN_SECONDS

        # Ερωτήσεις
        questions = (
            "**1. Πόσο χρονών είσαι;**\n"
            "**2. Πώς σε λένε στο Rolbox;**\n"
            "**3. Έχεις εμπειρία σε RP;**\n"
            "**4. Τι είναι το RDM;**\n"
            "**5. Πες μας 3 βασικά rules για εσένα**\n"
            "**6. Με ποιό κομμάτι του RP θες να ασχοληθεις;**\n"
            "**7. Πες μας το backstory του χαρακτήρα σου.**\n"
            "**8. Τι θα κάνεις αν κάποιος παίχτης κάνει επανειλημμένα failRP;**\n"
        )

        embed = discord.Embed(
            title="📋 Whitelist Application",
            description=f"{user.mention}, απάντησε στις παρακάτω ερωτήσεις:\n\n{questions}",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketCloseView())

        # Στέλνουμε στο review channel
        review_channel = guild.get_channel(WHITELIST_REVIEW_CHANNEL_ID)
        if review_channel:
            review_embed = discord.Embed(
                title="📝 Νέα Whitelist Αίτηση",
                description=f"Αίτηση από {user.mention} ({user.id})",
                color=discord.Color.blue()
            )
            review_embed.add_field(name="Ticket Channel", value=channel.mention, inline=False)
            review_embed.add_field(
                name="Οδηγία",
                value="Διαβάστε τις απαντήσεις στο ticket channel και πατήστε **Approve** ή **Deny**.",
                inline=False
            )

            review_msg = await review_channel.send(embed=review_embed, view=WhitelistReviewView())

            # Αποθήκευση δεδομένων
            whitelist_applications[review_msg.id] = {
                "user_id": user.id,
                "ticket_channel_id": channel.id
            }

        await interaction.response.send_message(
            f"Το whitelist application σου δημιουργήθηκε: {channel.mention}",
            ephemeral=True
        )

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
        title="🎫 Welcome to Paradox King Remastered",
        description=(
            "Για άμεση εξυπηρέτηση, επίλεξε την κατηγορία που ταιριάζει στο αίτημά σου.\n"
            "Η ομάδα μας θα σε εξυπηρετήσει το συντομότερο δυνατό."
        ),
        color=0x2b2d31  # premium dark
    )

    # FULL-WIDTH BANNER (όπως στη φωτογραφία)
    embed.set_image(url="https://cdn.discordapp.com/attachments/1392390677648893236/1392396770040324176/Jgt5WZxlUs17dbWZv0eZ1.jpeg")

    embed.set_footer(text="Paradox King Remastered • Support System")

    await ctx.send(embed=embed, view=MainTicketPanel())
    await ctx.reply("Το νέο ticket panel στάλθηκε.", delete_after=2)

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


# ================================
# EVENTS
# ================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ================================
# START (NO FLASK, NO KEEP_ALIVE)
# ================================

from keep_alive import keep_alive
keep_alive()

if __name__ == "__main__":
    bot.run(TOKEN)















