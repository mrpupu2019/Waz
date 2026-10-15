# 24/7 Quran / Waz / Gojol Discord Bot

A very simple, low-cost Discord voice bot. It sits in one voice channel 24/7 and plays Islamic audio (Quran tilawat, waz, gojol, Bangla Quran) from an online API. No commands. Everything is automatic.

---

## 1. What the bot does

| Situation | What happens |
|---|---|
| Bot starts | Joins your voice channel and stays there 24/7 (silent) |
| A person joins the channel | A random track starts playing |
| A track ends, people are still there | The next random track plays |
| The last person leaves | Music stops, bot stays connected |
| Someone joins again | Music starts again |
| Bot gets kicked or disconnected | It reconnects after 5 seconds |
| Someone drags the bot to another channel | It moves back to its own channel |
| A track link is broken | It skips to another track |

- **Status:** the bot's Discord status shows what's playing (for example "Listening to Surah 36 - Mishary Alafasy").
- **Sound quality:** audio is sent at your voice channel's bitrate. Raise it in Discord under Edit Channel → Bitrate (server boosts allow up to 384 kbps).
- **Low cost:** one small process. Audio streams directly from the source and nothing is downloaded or stored. There is no database, no website and no port.

---

## 2. Music sources (the `SOURCE` setting)

One bot uses one source. You change **only** `SOURCE` to change what it plays.

| Type | `SOURCE` value | Notes |
|---|---|---|
| Quran (public API) | `quran` | mp3quran.net free API. A random reciter (about 289 recitations) and a random surah each time. Default. |
| GitHub Pages folder | `https://mrpupu2019.github.io/waz/` | Plays every `.mp3` in the main folder of that GitHub repo. Example: `/gojol/` |
| archive.org item | `https://archive.org/details/full-al-quran-bangla` | Plays every original `.mp3` in that archive.org upload. Good for big collections. |

### How each source finds files
- **quran:** reads `https://mp3quran.net/api/v3/reciters` and builds links like `.../036.mp3`.
- **GitHub:** reads `https://api.github.com/repos/<user>/<repo>/contents/` and plays `https://<user>.github.io/<repo>/<file>.mp3`.
- **archive.org:** reads `https://archive.org/metadata/<item>` and plays `https://archive.org/download/<item>/<file>.mp3`.

The file list is loaded **once when the bot starts**. After you upload new files, restart the bot on Railway.

---

## 3. Project files

```
bot/
├── bot.py            # the whole bot (about 150 lines)
├── requirements.txt  # discord.py[voice], aiohttp
├── Dockerfile        # Python 3.12 slim + ffmpeg + opus
├── railway.json      # tells Railway to use the Dockerfile and always restart
└── README.md         # this guide
```

**Tech used:** Python 3.12, discord.py 2.7.1 (with Discord's newer voice encryption, called DAVE), ffmpeg (turns the mp3 into the Opus audio format Discord uses).

### Settings (environment variables)
| Variable | Required | Default | Meaning |
|---|---|---|---|
| `DISCORD_TOKEN` | Yes | – | Bot token from the Discord Developer Portal |
| `VOICE_CHANNEL_ID` | No | `952294021550719086` | Voice channel the bot stays in |
| `SOURCE` | No | `quran` | Music source (see section 2) |

The token is **never** written in the code. It only goes in Railway Variables.

---

## 4. A to Z setup guide

### Step A: Create the Discord bot
1. Go to https://discord.com/developers/applications → **New Application** → give it a name (for example "Quran 24/7").
2. In the left menu, open **Bot**:
   - Click **Reset Token** → **Copy**. Keep this secret. This is your `DISCORD_TOKEN`.
   - You don't need any Privileged Gateway Intents.
3. Optional: under **Bot**, set an avatar and name.

### Step B: Invite the bot to your server
1. Left menu → **OAuth2** → **URL Generator**.
2. Scopes: tick **bot**.
3. Bot Permissions: tick **View Channels**, **Connect** and **Speak**.
4. Copy the URL at the bottom, open it in your browser, pick your server and click **Authorize**.
5. If the voice channel is private, give the bot's role **View Channel / Connect / Speak** on that channel.

### Step C: Get the voice channel ID
1. Discord → **User Settings → Advanced → Developer Mode: ON**.
2. Right-click the voice channel → **Copy Channel ID**. This is your `VOICE_CHANNEL_ID`.

### Step D: Put the code on GitHub
1. Create a new GitHub repo (it can be private), for example `quran-bot`.
2. Upload the 5 files from the `bot/` folder into the main folder of the repo.
   (If you keep them inside a `bot/` folder instead, set **Root Directory = `bot`** in Railway, Step E.)

### Step E: Deploy on Railway
1. Go to https://railway.com → **New Project → Deploy from GitHub repo** → choose your repo.
2. Railway finds the `Dockerfile` and builds it on its own.
3. Open the service → **Variables** → add:
   ```
   DISCORD_TOKEN=your_token_here
   VOICE_CHANNEL_ID=952294021550719086
   SOURCE=quran
   ```
4. Railway redeploys. Open **Deployments → View Logs**. You should see:
   ```
   Loaded 289 tracks
   Connected to <your channel name>
   ```
5. Join the voice channel and the music starts.

You don't need a domain, port or database. Don't click "Generate Domain".

### Step F: Make more bots (Waz, Gojol, Bangla Quran...)
One bot can only be in one voice channel at a time, so each channel needs its own bot.
1. Make a **new Discord application/bot** (Step A) and invite it (Step B).
2. In Railway, add a **new service** from the same GitHub repo (or duplicate the service).
3. Set its Variables:
   ```
   DISCORD_TOKEN=<new bot token>
   VOICE_CHANNEL_ID=<that channel's ID>
   SOURCE=https://mrpupu2019.github.io/waz/
   ```
4. Do the same for Gojol (`.../gojol/`) or Bangla Quran (`https://archive.org/details/full-al-quran-bangla`).

The code stays the same for every bot. Only the variables change.

---

## 5. Adding your own music

### Option 1: GitHub Pages (small collections, under about 1 GB)
1. Create a **public** repo, for example `naat`.
2. Upload `.mp3` files to the main folder (names like `001.mp3`, `002.mp3` work well).
   - The website upload allows files up to 25 MB. For bigger files, use GitHub Desktop (up to 100 MB per file).
3. Go to Repo **Settings → Pages → Deploy from a branch → main / root → Save**.
4. `SOURCE=https://<your-user>.github.io/naat/`

### Option 2: archive.org (big collections, no size limit)
1. Make a free account at https://archive.org → **Upload**.
2. Drag in your mp3 files, add a title and an identifier (for example `my-waz-collection`), choose **Community Audio** → Upload.
3. Wait until processing finishes.
4. `SOURCE=https://archive.org/details/my-waz-collection`

### Turning a YouTube playlist into files
Install `yt-dlp` and `ffmpeg` on your PC, then run:
```
yt-dlp -x --audio-format mp3 --audio-quality 96K -o "%(playlist_index)03d.%(ext)s" "PLAYLIST_URL"
```
This gives `001.mp3`, `002.mp3`, and so on. Upload them using Option 1 or Option 2. Only use videos you are allowed to use.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| Logs say `KeyError: 'DISCORD_TOKEN'` | Add the `DISCORD_TOKEN` variable in Railway |
| `Improper token has been passed` | The token is wrong or was reset. Copy a new one. |
| Bot is online but not in the channel | Check `VOICE_CHANNEL_ID` and the bot's Connect/Speak permission |
| Bot joins but there is no sound | Check the bot is not server-muted and has Speak permission |
| Sound breaks up | Raise the channel bitrate. Check the Railway region (choose one near Discord's voice server for your area) |
| `Load failed, retrying in 60s` | The source website or API is down, or GitHub's rate limit was hit. The bot retries on its own. |
| New files are not playing | Restart the Railway service (the list is loaded when the bot starts) |

---

## 7. Cost tips (Railway)
- One service per bot. Each uses very little CPU and memory while idle and about one ffmpeg process while playing.
- When nobody is listening, nothing plays, so CPU use is close to zero.
- No volumes, databases or public domains are needed.

## 8. Security
- Never put the token in the code or share it in chat. If it leaks, click **Reset Token** right away and update Railway.
- Use a separate token for each bot.

## 9. Run on your own PC (optional)
```
pip install -r requirements.txt     # also install ffmpeg
DISCORD_TOKEN=xxx VOICE_CHANNEL_ID=123 SOURCE=quran python bot.py
```
