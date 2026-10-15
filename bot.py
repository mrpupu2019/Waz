import os
import random
import time
import asyncio
import aiohttp
import discord
from urllib.parse import quote, unquote

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ.get("VOICE_CHANNEL_ID", "952294021550719086"))
# "quran", a GitHub Pages folder URL, or an archive.org/details/ URL
SOURCE = os.environ.get("SOURCE", "quran").strip()

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
    "options": "-vn",
}

intents = discord.Intents.none()
intents.guilds = True
intents.voice_states = True
client = discord.Client(intents=intents)

reciters = []
waz_files = []
WAZ_BASE = ""
lock = asyncio.Lock()
started = 0.0


async def load_sources():
    global reciters, waz_files, WAZ_BASE
    async with aiohttp.ClientSession() as s:
        if SOURCE.lower() == "quran":
            async with s.get("https://mp3quran.net/api/v3/reciters?language=eng") as r:
                data = await r.json(content_type=None)
            for rec in data["reciters"]:
                for m in rec["moshaf"]:
                    surahs = [int(x) for x in m["surah_list"].split(",") if x]
                    reciters.append((rec["name"], m["server"], surahs))
        elif "archive.org/details/" in SOURCE:
            item = SOURCE.rstrip("/").split("/details/")[1].split("/")[0]
            WAZ_BASE = f"https://archive.org/download/{item}/"
            async with s.get(f"https://archive.org/metadata/{item}") as r:
                data = await r.json(content_type=None)
            waz_files = sorted(quote(f["name"]) for f in data["files"]
                               if f["name"].lower().endswith(".mp3") and f.get("source") == "original")
        else:
            WAZ_BASE = SOURCE.rstrip("/") + "/"
            owner = WAZ_BASE.split("//")[1].split(".")[0]
            repo = WAZ_BASE.split("/")[3]
            async with s.get(f"https://api.github.com/repos/{owner}/{repo}/contents/") as r:
                data = await r.json(content_type=None)
            waz_files = sorted(f["name"] for f in data if f["name"].lower().endswith(".mp3"))
    print(f"Loaded {len(reciters) or len(waz_files)} tracks")


def pick_track():
    if reciters:
        name, server, surahs = random.choice(reciters)
        n = random.choice(surahs)
        return f"{server}{n:03d}.mp3", f"Surah {n} - {name}"
    f = random.choice(waz_files)
    return WAZ_BASE + f, unquote(f)[:-4].replace("_", " ")[:120]


def has_listeners(vc):
    return vc and vc.channel and any(not m.bot for m in vc.channel.members)


async def play_next():
    async with lock:
        if time.monotonic() - started < 5:
            await asyncio.sleep(5)
        for _ in range(5):
            if await try_play():
                return
            await asyncio.sleep(2)


async def try_play():
    vc = client.get_channel(CHANNEL_ID).guild.voice_client
    if not vc or not vc.is_connected() or vc.is_playing():
        return True
    if not has_listeners(vc):
        await client.change_presence(activity=None)
        return True
    url, title = pick_track()
    try:
        audio = discord.FFmpegOpusAudio(url, bitrate=vc.channel.bitrate // 1000, **FFMPEG_OPTS)
    except Exception as e:
        print(f"Failed {url}: {e}")
        return False
    global started
    started = time.monotonic()
    vc.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(), client.loop))
    print(f"Playing: {title}")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=title))
    return True


async def connect():
    channel = client.get_channel(CHANNEL_ID)
    vc = channel.guild.voice_client
    if vc and vc.is_connected():
        if vc.channel.id != CHANNEL_ID:
            await vc.move_to(channel)
        return
    if vc:
        await vc.disconnect(force=True)
    await channel.connect(reconnect=True, self_deaf=True)
    print(f"Connected to {channel.name}")
    await play_next()


@client.event
async def on_ready():
    while not reciters and not waz_files:
        try:
            await load_sources()
        except Exception as e:
            print(f"Load failed, retrying in 60s: {e}")
            await asyncio.sleep(60)
    await connect()


@client.event
async def on_voice_state_update(member, before, after):
    if member.id == client.user.id:
        if after.channel is None or after.channel.id != CHANNEL_ID:
            await asyncio.sleep(5)
            await connect()
        return
    if member.bot:
        return
    vc = member.guild.voice_client
    if not vc:
        return
    if after.channel and after.channel.id == CHANNEL_ID:
        await play_next()
    elif before.channel and before.channel.id == CHANNEL_ID and not has_listeners(vc):
        vc.stop()
        print("Channel empty, stopped")


client.run(TOKEN)
