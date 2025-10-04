# 🍿 Popcorn Telegram Bot (Heroku Ready)

A full-featured Telegram movie bot built with `python-telegram-bot`.

## 🚀 1-Click Deploy

Click the button below to deploy this bot directly to Heroku 👇

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/the-stonex/PopcornMovieBot)

---

## 🧩 Environment Variables

| Variable | Description |
|-----------|--------------|
| `BOT_TOKEN` | Your Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `PUBLIC_CHANNEL` | Public channel username (like `@popcornmovies`) |
| `PRIVATE_CHANNEL` | Private channel ID (like `-1001234567890`) |
| `PRIVATE_INVITE` | Invite link to private channel |
| `SECOND_BOT_USERNAME` | Helper bot username without @ |
| `LOG_GROUP_ID` | Log group ID (like `-1009876543210`) |
| `BOT_USERNAME` | Main bot username (without @) |
| `TMDB_API_KEY` | TheMovieDB API key (optional) |

---

## 💡 How to Get IDs

- Channel or group ID ➜ use [@RawDataBot](https://t.me/RawDataBot)
- TMDb API key ➜ https://www.themoviedb.org/settings/api
- Make sure your bot is **member** of both channels.

---

## ⚙️ Manual Deploy (CLI)

```bash
git clone https://github.com/the-stonex/PopcornMovieBot
cd PopcornMovieBot
heroku create
git push heroku master
heroku ps:scale worker=1
heroku logs --tail
