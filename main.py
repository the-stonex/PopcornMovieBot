import os
import logging
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- Config from ENV ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PUBLIC_CHANNEL = os.environ.get("PUBLIC_CHANNEL", "@yourpublic")
PRIVATE_CHANNEL = os.environ.get("PRIVATE_CHANNEL", "-100123")
PRIVATE_INVITE = os.environ.get("PRIVATE_INVITE", "")
SECOND_BOT_USERNAME = os.environ.get("SECOND_BOT_USERNAME", "")
LOG_GROUP_ID = int(os.environ.get("LOG_GROUP_ID", "0"))
BOT_USERNAME = os.environ.get("BOT_USERNAME", "PopcornMovieBot")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")

TMDB_IMG = "https://image.tmdb.org/t/p/w500"

# ---------- Check Membership ----------
async def is_user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        pub = await context.bot.get_chat_member(PUBLIC_CHANNEL, user_id)
        priv = await context.bot.get_chat_member(PRIVATE_CHANNEL, user_id)
        return (pub.status in ["member", "administrator", "creator"]) and (
            priv.status in ["member", "administrator", "creator"]
        )
    except Exception as e:
        logger.warning(f"Membership check error: {e}")
        return False


# ---------- Force Join Screen ----------
async def send_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    keyboard = [
        [InlineKeyboardButton("📢 Join Public Channel", url=f"https://t.me/{PUBLIC_CHANNEL.replace('@','')}")],
        [InlineKeyboardButton("🔒 Join Private Channel", url=PRIVATE_INVITE or "https://t.me/")],
        [InlineKeyboardButton("🤖 Start Helper Bot", url=f"https://t.me/{SECOND_BOT_USERNAME}?start=start")],
        [InlineKeyboardButton("✅ I Completed All", callback_data="recheck_all")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = (
        "⚠️ *आपने सभी स्टेप पूरे नहीं किए हैं!*\n\n"
        "कृपया नीचे दिए गए चरण पूरे करें:\n"
        "1️⃣ Public Channel Join करें\n"
        "2️⃣ Private Channel Join करें\n"
        "3️⃣ Helper Bot को Start करें\n\n"
        "फिर '✅ I Completed All' पर क्लिक करें ✅"
    )
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)


# ---------- Log New User ----------
async def log_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        "📥 *New User Started Bot*\n\n"
        f"👤 Name: {user.full_name}\n"
        f"🧾 Username: @{user.username if user.username else 'No Username'}\n"
        f"🆔 ID: `{user.id}`"
    )
    if LOG_GROUP_ID:
        try:
            await context.bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Log error: {e}")


# ---------- Welcome Screen ----------
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE, query=False):
    text = (
        "🍿 *WELCOME TO POPCORN BOT* 🎬\n\n"
        "अब आप कोई भी मूवी या वेब सीरीज़ सर्च कर सकते हैं!\n"
        "👇 नीचे दिए गए बटन से शुरू करें 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🔎 Search Movies or Series", switch_inline_query_current_chat="")],
        [
            InlineKeyboardButton("🔥 Trending", callback_data="trending"),
            InlineKeyboardButton("🎬 Now Playing", callback_data="now_playing"),
        ],
        [InlineKeyboardButton("📢 Share Bot", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if query and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)


# ---------- /start Command ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_new_user(update, context)
    if not await is_user_joined(update, context):
        await send_force_join(update, context)
        return
    await send_welcome(update, context)


# ---------- Recheck ----------
async def recheck_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_user_joined(update, context):
        await send_welcome(update, context, query=True)
    else:
        await send_force_join(update, context, edit=True)


# ---------- TMDb API Helpers ----------
def tmdb_search(query):
    if not TMDB_API_KEY:
        return None
    url = f"https://api.themoviedb.org/3/search/multi"
    params = {"api_key": TMDB_API_KEY, "query": query, "language": "en-US"}
    r = requests.get(url, params=params)
    return r.json() if r.status_code == 200 else None


def tmdb_trending():
    if not TMDB_API_KEY:
        return None
    url = f"https://api.themoviedb.org/3/trending/all/week?api_key={TMDB_API_KEY}&language=en-US"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None


def tmdb_now_playing():
    if not TMDB_API_KEY:
        return None
    url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=en-US"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None


# ---------- Callback Handler ----------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "trending":
        result = tmdb_trending()
        if not result or not result.get("results"):
            await query.edit_message_text("No trending results found.")
            return
        msg = "*🔥 Trending This Week:*\n\n"
        for i, m in enumerate(result["results"][:10], 1):
            title = m.get("title") or m.get("name")
            date = m.get("release_date") or m.get("first_air_date") or "N/A"
            msg += f"{i}. *{title}* ({date})\n"
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif data == "now_playing":
        result = tmdb_now_playing()
        if not result or not result.get("results"):
            await query.edit_message_text("No now playing results found.")
            return
        msg = "*🎬 Now Playing in Theatres:*\n\n"
        for i, m in enumerate(result["results"][:10], 1):
            title = m.get("title")
            date = m.get("release_date") or "N/A"
            msg += f"{i}. *{title}* ({date})\n"
        await query.edit_message_text(msg, parse_mode="Markdown")


# ---------- Message Handler ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_joined(update, context):
        await send_force_join(update, context)
        return

    query = update.message.text.strip()
    if not TMDB_API_KEY:
        await update.message.reply_text(f"🔍 You searched: *{query}*", parse_mode="Markdown")
        return

    await update.message.reply_text(f"🔍 Searching for *{query}* ...", parse_mode="Markdown")
    data = tmdb_search(query)
    if not data or not data.get("results"):
        await update.message.reply_text("❌ कोई रिज़ल्ट नहीं मिला।")
        return

    item = data["results"][0]
    title = item.get("title") or item.get("name") or "Unknown"
    overview = item.get("overview") or "No description available."
    poster = item.get("poster_path")

    caption = f"*{title}*\n\n{overview}"
    if poster:
        try:
            await update.message.reply_photo(photo=TMDB_IMG + poster, caption=caption, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")


# ---------- Main ----------
def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(recheck_all, pattern="recheck_all"))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Popcorn Bot started successfully!")
    app.run_polling()


if __name__ == "__main__":
    main()
