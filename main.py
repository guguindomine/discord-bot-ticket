import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime
import asyncio

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CATEGORY_ID = int(os.getenv('CATEGORY_ID', 0))
STAFF_ROLE_ID = int(os.getenv('STAFF_ROLE_ID', 0))
VOUCH_CHANNEL_ID = int(os.getenv('VOUCH_CHANNEL_ID', 0))
HELPER_CHANNEL_ID = int(os.getenv('HELPER_CHANNEL_ID', 0))

# Store vouches
vouches = {}

class TicketControlView(discord.ui.View):
    def __init__(self, user_id: int, game: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.game = game

    @discord.ui.button(label="✅ Vouch", style=discord.ButtonStyle.green, custom_id="vouch_button")
    async def vouch_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            await interaction.response.send_message(
                "❌ You can't vouch for yourself!",
                ephemeral=True
            )
            return

        # Record the vouch
        booster = interaction.user
        if booster.id not in vouches:
            vouches[booster.id] = []
        
        vouches[booster.id].append({
            "user": self.user_id,
            "game": self.game,
            "date": datetime.now(),
            "booster_name": booster.name
        })

        # Response message
        response_embed = discord.Embed(
            title="⭐ Vouch Recorded!",
            color=0x7289DA,
            description=f"Great work, {booster.mention}!"
        )
        response_embed.add_field(
            name="👤 Booster",
            value=booster.mention,
            inline=True
        )
        response_embed.add_field(
            name="🎮 Game",
            value=self.game,
            inline=True
        )
        response_embed.add_field(
            name="⭐ Total Vouches",
            value=f"**{len(vouches[booster.id])}**",
            inline=True
        )
        response_embed.set_footer(text="This vouch is visible on the booster's profile!")
        
        await interaction.response.send_message(embed=response_embed, ephemeral=False)

        # Post to vouch channel if configured
        if VOUCH_CHANNEL_ID != 0:
            vouch_channel = interaction.guild.get_channel(VOUCH_CHANNEL_ID)
            if vouch_channel:
                vouch_embed = discord.Embed(
                    title="⭐ NEW VOUCH!",
                    color=0x7289DA,
                    timestamp=datetime.now()
                )
                vouch_embed.add_field(name="🏆 Booster", value=booster.mention, inline=False)
                vouch_embed.add_field(name="👤 Customer", value=f"<@{self.user_id}>", inline=False)
                vouch_embed.add_field(name="🎮 Game", value=self.game, inline=False)
                vouch_embed.add_field(name="⭐ Booster's Vouches", value=f"**{len(vouches[booster.id])}** total", inline=False)
                vouch_embed.set_footer(text="Keep providing excellent service!")
                await vouch_channel.send(embed=vouch_embed)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_button")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            # Allow staff to close too
            staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
            if not (staff_role and staff_role in interaction.user.roles):
                await interaction.response.send_message(
                    "❌ Only the ticket creator or staff can close this ticket!",
                    ephemeral=True
                )
                return

        close_embed = discord.Embed(
            title="🔒 Ticket Closed",
            color=0x7289DA,
            description="Thank you for using PARADOX! We hope to see you again soon."
        )
        close_embed.add_field(name="📋 Game", value=self.game, inline=True)
        close_embed.add_field(name="⏱️ Duration", value="Closed by " + interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=close_embed)
        
        # Delete the channel after a short delay
        await asyncio.sleep(2)
        await interaction.channel.delete()

class ParadoxTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view for 24/7 operation

    @discord.ui.select(
        custom_id="paradox_selector",
        placeholder="Select a game to start your ticket!",
        options=[
            discord.SelectOption(label="Anime Last Stand (ALS)", emoji="⚔️", value="ALS"),
            discord.SelectOption(label="Anime Guardians (AG)", emoji="👻", value="AG"),
            discord.SelectOption(label="Anime Crusaders (AC)", emoji="🗡️", value="AC"),
            discord.SelectOption(label="Universal Tower Defense (UTD)", emoji="🌍", value="UTD"),
            discord.SelectOption(label="Anime Vanguards (AV)", emoji="🛡️", value="AV"),
            discord.SelectOption(label="Bizarre Lineage (BL)", emoji="💫", value="BL"),
            discord.SelectOption(label="Sailor Piece (SP)", emoji="⛵", value="SP"),
            discord.SelectOption(label="Anime Rangers X (ARX)", emoji="🔥", value="ARX"),
            discord.SelectOption(label="All Star Tower Defense (ASTD)", emoji="⭐", value="ASTD"),
            discord.SelectOption(label="Anime Overload (AOL)", emoji="👑", value="AOL"),
        ]
    )
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)

        if not category:
            await interaction.response.send_message(
                "❌ Category not configured. Contact an admin.",
                ephemeral=True
            )
            return

        # Create private channel permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"carry-{select.values[0]}-{user.name}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

        # Welcome embed inside the ticket
        embed = discord.Embed(
            title="⚔️ PARADOX | Carry Service",
            color=0x7289DA,
            description=f"Welcome {user.mention}! A professional booster will help you shortly."
        )
        
        game_emojis = {"ALS": "⚔️", "AV": "🛡️", "ASTD": "⭐"}
        game_names = {"ALS": "Anime Last Stand", "AV": "Anime Vanguards", "ASTD": "All Star Tower Defense"}
        selected_game = select.values[0]
        
        embed.add_field(
            name=f"{game_emojis.get(selected_game, '✨')} Service Type",
            value=game_names.get(selected_game, selected_game),
            inline=False
        )
        embed.add_field(
            name="👤 Customer",
            value=user.mention,
            inline=True
        )
        embed.add_field(
            name="⏱️ Status",
            value="🟢 Awaiting Booster",
            inline=True
        )
        
        embed.set_footer(text="React with ⭐ to vouch when complete!")
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await channel.send(embed=embed, view=TicketControlView(user.id, select.values[0]))


class HelperApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="helper_selector",
        placeholder="Select your specialty!",
        options=[
            discord.SelectOption(label="Anime Last Stand (ALS)", emoji="⚔️", value="ALS"),
            discord.SelectOption(label="Anime Guardians (AG)", emoji="👻", value="AG"),
            discord.SelectOption(label="Anime Crusaders (AC)", emoji="🗡️", value="AC"),
            discord.SelectOption(label="Universal Tower Defense (UTD)", emoji="🌍", value="UTD"),
            discord.SelectOption(label="Anime Vanguards (AV)", emoji="🛡️", value="AV"),
            discord.SelectOption(label="Bizarre Lineage (BL)", emoji="💫", value="BL"),
            discord.SelectOption(label="Sailor Piece (SP)", emoji="⛵", value="SP"),
            discord.SelectOption(label="Anime Rangers X (ARX)", emoji="🔥", value="ARX"),
            discord.SelectOption(label="All Star Tower Defense (ASTD)", emoji="⭐", value="ASTD"),
            discord.SelectOption(label="Anime Overload (AOL)", emoji="👑", value="AOL"),
        ]
    )
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        user = interaction.user
        specialty = select.values[0]
        
        # Game names mapping
        game_names = {
            "ALS": "Anime Last Stand",
            "AG": "Anime Guardians",
            "AC": "Anime Crusaders",
            "UTD": "Universal Tower Defense",
            "AV": "Anime Vanguards",
            "BL": "Bizarre Lineage",
            "SP": "Sailor Piece",
            "ARX": "Anime Rangers X",
            "ASTD": "All Star Tower Defense",
            "AOL": "Anime Overload"
        }
        
        # Create application embed
        embed = discord.Embed(
            title="📋 Helper Application Submitted",
            color=0x7289DA,
            description=f"Thank you for applying, {user.mention}!"
        )
        
        embed.add_field(name="👤 Applicant", value=user.mention, inline=True)
        embed.add_field(name="🎮 Specialty", value=game_names.get(specialty, specialty), inline=True)
        embed.add_field(name="⏱️ Status", value="⏳ Pending Review", inline=True)
        embed.set_footer(text="Staff will review your application soon!")
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ParadoxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # REQUIRED for !setup to work
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Keeps the dropdown working after restarts
        self.add_view(ParadoxTicketView())
        self.add_view(TicketControlView(0, ""))

    async def on_ready(self):
        print(f"✅ Bot logged in as {self.user}")


bot = ParadoxBot()


@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """Creates the ticket system embed"""
    if CATEGORY_ID == 0 or STAFF_ROLE_ID == 0:
        await ctx.send(
            "❌ Bot not configured. Set CATEGORY_ID and STAFF_ROLE_ID in .env file."
        )
        return

    embed = discord.Embed(
        title="🎮 PARADOX | Carry Requests",
        color=0x7289DA
    )
    
    embed.add_field(
        name="Welcome to our Carry Service!",
        value="Your reliable place for fast and professional anime carries.",
        inline=False
    )
    
    embed.add_field(
        name="🎯 FREE SERVICE",
        value="We help you complete runs for free — no hidden fees, no premium memberships.",
        inline=False
    )
    
    embed.add_field(
        name="👻 BOOSTER PERKS",
        value="Professional boosters earn reputation through customer vouches and build trust in the community.",
        inline=False
    )
    
    embed.add_field(
        name="⚡ QUICK SUPPORT",
        value="Get connected with experienced boosters usually within minutes. Fast responses & quality service.",
        inline=False
    )
    
    embed.add_field(
        name="📋 HOW IT WORKS",
        value="Simply select your game from the menu below to start your ticket!",
        inline=False
    )
    
    games_list = (
        "⚔️ Anime Last Stand (ALS)\n"
        "� Anime Guardians (AG)\n"
        "🗡️ Anime Crusaders (AC)\n"
        "🌍 Universal Tower Defense (UTD)\n"
        "🛡️ Anime Vanguards (AV)\n"
        "💫 Bizarre Lineage (BL)\n"
        "⛵ Sailor Piece (SP)\n"
        "🔥 Anime Rangers X (ARX)\n"
        "⭐ All Star Tower Defense (ASTD)\n"
        "👑 Anime Overload
     (AOL)"
    )
    
    embed.add_field(
        name="🎮 Supported Games:",
        value=games_list,
        inline=False
    )
    
    embed.set_footer(text="Select your game below to get started!")
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    
    await ctx.send(embed=embed, view=ParadoxTicketView())


@bot.command()
async def vouches(ctx, user: discord.User = None):
    """Check vouches for a booster"""
    target = user or ctx.author
    
    if target.id not in vouches or len(vouches[target.id]) == 0:
        embed = discord.Embed(
            title="⭐ Booster Vouches",
            description=f"**{target.name}** hasn't earned any vouches yet! 🌱",
            color=0x7289DA
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
        return
    
    vouch_list = vouches[target.id]
    
    # Count vouches by game
    game_count = {}
    for vouch in vouch_list:
        game = vouch["game"]
        game_count[game] = game_count.get(game, 0) + 1
    
    game_emojis = {"ALS": "⚔️", "AV": "🛡️", "ASTD": "⭐"}
    game_names = {"ALS": "Anime Last Stand", "AV": "Anime Vanguards", "ASTD": "All Star Tower Defense"}
    
    vouch_embed = discord.Embed(
        title=f"⭐ Booster Profile",
        color=0x7289DA,
        description=f"Professional booster with **{len(vouch_list)}** successful carries!"
    )
    
    vouch_embed.add_field(
        name="👤 Booster",
        value=target.mention,
        inline=False
    )
    
    vouch_embed.add_field(
        name="🏆 Total Vouches",
        value=f"**{len(vouch_list)}** ⭐",
        inline=True
    )
    
    vouch_embed.add_field(
        name="📊 Success Rate",
        value=f"**100%** (All satisfied customers)",
        inline=True
    )
    
    # Add game breakdown
    game_field = ""
    for game in ["ALS", "AV", "ASTD"]:
        if game in game_count:
            count = game_count[game]
            emoji = game_emojis.get(game, "✨")
            name = game_names.get(game, game)
            game_field += f"{emoji} {name}: **{count}** vouch{'es' if count > 1 else ''}\n"
    
    if game_field:
        vouch_embed.add_field(
            name="🎮 Specialties",
            value=game_field.strip(),
            inline=False
        )
    
    vouch_embed.set_thumbnail(url=target.display_avatar.url)
    vouch_embed.set_footer(text="These vouches represent satisfied customers!")
    
    await ctx.send(embed=vouch_embed)


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN not found in .env file")
    bot.run(TOKEN)
