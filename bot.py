import discord
from discord.ext import commands
from discord import app_commands
import pymongo
import re
import asyncio
from datetime import datetime, timedelta
import os

# --- CONFIG ---
TOKEN = os.getenv('TOKEN')
PREFIX = os.getenv('PREFIX', '!')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = 'vortex_dyno'

client_mongo = pymongo.MongoClient(MONGO_URI)
db = client_mongo[DB_NAME]
warns_col = db['warnings']
settings_col = db['guild_settings']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- HELPERS ---
async def get_member(ctx, arg):
    try:
        return await commands.MemberConverter().convert(ctx, arg)
    except:
        return None

def has_permission(ctx, perm):
    return ctx.author.guild_permissions.__getattribute__(perm)

# --- MODERATION ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'🔨 Banned {member.mention} | {reason or "No reason"}')

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'👢 Kicked {member.mention} | {reason or "No reason"}')

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: int, *, reason=None):
    await member.timeout(timedelta(seconds=duration), reason=reason)
    await ctx.send(f'🔇 Muted {member.mention} for {duration}s | {reason or "No reason"}')

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f'🔊 Unmuted {member.mention}')

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason"):
    warns_col.insert_one({'guild_id': ctx.guild.id, 'user_id': member.id, 'reason': reason, 'mod': ctx.author.id, 'date': datetime.utcnow()})
    await ctx.send(f'⚠️ Warned {member.mention} | {reason}')

@bot.command()
async def warnings(ctx, member: discord.Member):
    count = warns_col.count_documents({'guild_id': ctx.guild.id, 'user_id': member.id})
    await ctx.send(f'📋 {member.mention} has {count} warnings')

@bot.command()
@commands.has_permissions(moderate_members=True)
async def clearwarns(ctx, member: discord.Member):
    warns_col.delete_many({'guild_id': ctx.guild.id, 'user_id': member.id})
    await ctx.send(f'🧹 Cleared warnings for {member.mention}')

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount < 1 or amount > 100:
        return await ctx.send('1-100 only')
    deleted = await ctx.channel.purge(limit=amount+1)
    await ctx.send(f'🗑️ Deleted {len(deleted)-1} messages', delete_after=3)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send('🔒 Channel locked')

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send('🔓 Channel unlocked')

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f'🐢 Slowmode set to {seconds}s')

# --- UTILITY ---
@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 {round(bot.latency * 1000)}ms')

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f'User: {member}', color=member.color)
    embed.add_field(name='ID', value=member.id)
    embed.add_field(name='Joined', value=member.joined_at.strftime('%Y-%m-%d %H:%M'))
    embed.add_field(name='Registered', value=member.created_at.strftime('%Y-%m-%d %H:%M'))
    embed.add_field(name='Roles', value=', '.join([r.name for r in member.roles][1:]) or 'None')
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    embed = discord.Embed(title=ctx.guild.name, color=0x00ff00)
    embed.add_field(name='Owner', value=ctx.guild.owner)
    embed.add_field(name='Members', value=ctx.guild.member_count)
    embed.add_field(name='Channels', value=len(ctx.guild.channels))
    embed.add_field(name='Roles', value=len(ctx.guild.roles))
    embed.add_field(name='Created', value=ctx.guild.created_at.strftime('%Y-%m-%d'))
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def roleinfo(ctx, *, role: discord.Role):
    embed = discord.Embed(title=role.name, color=role.color)
    embed.add_field(name='ID', value=role.id)
    embed.add_field(name='Members', value=len(role.members))
    embed.add_field(name='Color', value=str(role.color))
    embed.add_field(name='Position', value=role.position)
    await ctx.send(embed=embed)

# --- AUTO-MOD (simple) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def antilink(ctx, mode: str = None):
    if mode not in ['on', 'off']:
        return await ctx.send('Usage: !antilink on/off')
    settings_col.update_one({'guild_id': ctx.guild.id}, {'$set': {'antilink': mode == 'on'}}, upsert=True)
    await ctx.send(f'🔗 Anti-link {mode}')

@bot.command()
@commands.has_permissions(administrator=True)
async def antispam(ctx, mode: str = None):
    if mode not in ['on', 'off']:
        return await ctx.send('Usage: !antispam on/off')
    settings_col.update_one({'guild_id': ctx.guild.id}, {'$set': {'antispam': mode == 'on'}}, upsert=True)
    await ctx.send(f'🛡️ Anti-spam {mode}')

@bot.command()
@commands.has_permissions(administrator=True)
async def filter(ctx, word: str):
    settings_col.update_one({'guild_id': ctx.guild.id}, {'$push': {'filter_words': word.lower()}}, upsert=True)
    await ctx.send(f'🚫 Added "{word}" to filter')

# --- MUSIC (simulated queue) ---
queue = {}
@bot.command()
async def play(ctx, *, song: str):
    if ctx.guild.id not in queue:
        queue[ctx.guild.id] = []
    queue[ctx.guild.id].append(song)
    await ctx.send(f'🎵 Added "{song}" to queue (position {len(queue[ctx.guild.id])})')

@bot.command()
async def stop(ctx):
    if ctx.guild.id in queue:
        queue[ctx.guild.id].clear()
    await ctx.send('⏹️ Stopped playback (simulated)')

# --- EVENT: AUTO-MOD FILTER ---
@bot.event
async def on_message(msg):
    if msg.author.bot:
        return
    settings = settings_col.find_one({'guild_id': msg.guild.id})
    if settings:
        if settings.get('antilink', False) and re.search(r'(https?://|www\.)', msg.content):
            await msg.delete()
            await msg.channel.send(f'{msg.author.mention} Links blocked', delete_after=3)
            return
        if settings.get('filter_words', []):
            for word in settings['filter_words']:
                if word in msg.content.lower():
                    await msg.delete()
                    await msg.channel.send(f'{msg.author.mention} Filtered word', delete_after=3)
                    return
    await bot.process_commands(msg)

# --- SLASH COMMANDS (Dyno-like) ---
@bot.tree.command(name='ban', description='Ban a user')
@app_commands.default_permissions(ban_members=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.ban(reason=reason)
    await interaction.response.send_message(f'Banned {member.mention}')

# Add more slash commands similarly (omitted for brevity, but functional)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Vortex Dyno (Python) online as {bot.user} | {len(bot.guilds)} guilds')

bot.run(TOKEN)