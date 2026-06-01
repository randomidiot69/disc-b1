import discord
import random
from discord.ext import commands
import os
import time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CACHE_DURATION = 3600  # 1 hour

cached_pools = None
cache_timestamp = 0

SOURCE_CHANNEL_ID = 1497296815559544862
TARGET_CHANNEL_ID = 1498464307195936858


# ─────────────────────────────
# THREAD TIERS
# ─────────────────────────────

COMMON_THREAD_IDS = {
    1501682879682318346,
    1501682789051793660,
    1501682682105561128,
    1501682600845250724,
    1501682518565589002,
    1501682458394103921,
    1501682390748102866
}
UNCOMMON_THREAD_IDS = {
    1497297219328409673,
    1497297722947010591,
    1497298131971211304,
    1497299464048873692,
    1497300316910260314,
    1497301044873396374
}
RARE_THREAD_IDS = {
    1498027467280089261,
    1498070775452925952,
    1498076218069614625,
    1498077077306605658,
    1498084047690399895,
    1498086692341682256
}
SUPER_RARE_THREAD_IDS = {
    1501684667441479801,
    1501684608461177083,
    1501684510151147564,
    1501684444698771456,
    1501684384980533308,
    1501684322531414218,
    1501683075422093332
}
EPIC_THREAD_IDS = {
    1501702000151236809 
}
LEGENDARY_THREAD_IDS = {
    1501686335906254869
}


# ─────────────────────────────
# STATS
# ─────────────────────────────

stats_counter = {
    "A": 0,
    "B": 0,
    "C": 0,
    "D": 0,
    "E": 0,
    "F": 0
}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ─────────────────────────────
# THREAD LOADER
# ─────────────────────────────

async def get_all_threads(channel):
    threads = []
    threads.extend(channel.threads)

    async for t in channel.archived_threads(limit=None):
        threads.append(t)

    return threads


async def collect_messages(channel):
    global cached_pools, cache_timestamp

    now = time.time()

    # Use cache if still valid
    if cached_pools and (now - cache_timestamp) < CACHE_DURATION:
        return cached_pools

    threads = await get_all_threads(channel)

    pools = {
        "A": [],
        "B": [],
        "C": [],
        "D": [],
        "E": [],
        "F": []
    }

    for thread in threads:

        async for msg in thread.history(limit=100):
            if msg.author.bot:
                continue

            if thread.id in COMMON_THREAD_IDS:
                pools["A"].append(msg)

            elif thread.id in UNCOMMON_THREAD_IDS:
                pools["B"].append(msg)

            elif thread.id in RARE_THREAD_IDS:
                pools["C"].append(msg)

            elif thread.id in SUPER_RARE_THREAD_IDS:
                pools["D"].append(msg)

            elif thread.id in EPIC_THREAD_IDS:
                pools["E"].append(msg)

            elif thread.id in LEGENDARY_THREAD_IDS:
                pools["F"].append(msg)

    cached_pools = pools
    cache_timestamp = now

    print("Pools rebuilt from Discord.")

    return pools

# ─────────────────────────────
# MESSAGE HANDLING
# ─────────────────────────────

def extract_text(message):
    parts = []

    if message.content:
        parts.append(message.content)

    if message.embeds:
        e = message.embeds[0]
        if e.title:
            parts.append(e.title)
        if e.description:
            parts.append(e.description)

    return "\n".join(parts).strip()


async def send_message(message, channel):
    content = extract_text(message)

    files = []
    for att in message.attachments:
        try:
            files.append(await att.to_file())
        except:
            pass

    if files:
        await channel.send(content=content or None, files=files)
    else:
        await channel.send(content=content or "(No content)")


# ─────────────────────────────
# TIER PICKER
# ─────────────────────────────

def pick_tier():

    r = random.random()

    # 2.5%
    if r < 0.025:
        return "F"  # Legendary

    # 0.9%
    elif r < 0.034:
        return "E"  # Epic

    # 8%
    elif r < 0.114:
        return "D"  # Super Rare

    # 8%
    elif r < 0.194:
        return "C"  # Rare

    # 35%
    elif r < 0.544:
        return "B"  # Uncommon

    # 45.6%
    else:
        return "A"  # Common


# ─────────────────────────────
# MAIN COMMAND
# ─────────────────────────────

@bot.command()
async def roll(ctx, amount: int):

    if amount <= 0:
        await ctx.send("Give me a number above 0.")
        return

    if amount > 100:
        await ctx.send("Max 100 rolls.")
        return

    source = bot.get_channel(SOURCE_CHANNEL_ID)
    target = bot.get_channel(TARGET_CHANNEL_ID)

    if not source or not target:
        await ctx.send("Channel not found.")
        return

    pools = await collect_messages(source)

    used = set()
    sent = 0
    attempts = 0
    max_attempts = amount * 15

    # ───────── NEW: recap storage ─────────
    recap_texts = []

    while sent < amount and attempts < max_attempts:
        attempts += 1

        tier = pick_tier()
        pool = pools.get(tier, [])

        if not pool:
            pool = pools["A"]

        if not pool:
            continue

        msg = random.choice(pool)

        if msg.id in used:
            continue

        used.add(msg.id)

        await send_message(msg, target)

        text = extract_text(msg)
        if text:
            recap_texts.append(text)

        stats_counter[tier] += 1
        sent += 1

    # ───────── FINAL RECAP MESSAGE ─────────
    if recap_texts:
        formatted = "; ".join(f"`{t}`" for t in recap_texts)

        await target.send(
            f"{ctx.author.mention}, your last {len(recap_texts)} rolls:\n{formatted}"
        )


# ─────────────────────────────
# STATS
# ─────────────────────────────

@bot.command()
async def stats(ctx):

    total = sum(stats_counter.values())

    if total == 0:
        await ctx.send("No rolls yet.")
        return

    await ctx.send(
        "📊 **Tier Stats**\n"
        f"A (Common): {stats_counter['A']}\n"
        f"B (Uncommon): {stats_counter['B']}\n"
        f"C (Rare): {stats_counter['C']}\n"
        f"D (Super Rare): {stats_counter['D']}\n"
        f"E (Epic): {stats_counter['E']}\n"
        f"F (Legendary): {stats_counter['F']}\n"
    )


@bot.command()
async def resetstats(ctx):
    global stats_counter
    stats_counter = {k: 0 for k in stats_counter}
    await ctx.send("📊 Stats reset.")

@bot.command()
async def clearcache(ctx):
    global cached_pools, cache_timestamp

    cached_pools = None
    cache_timestamp = 0

    await ctx.send("🔄 Cache cleared.")
bot.run(TOKEN)
