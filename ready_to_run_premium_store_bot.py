# READY-TO-RUN TELEGRAM STORE BOT — LEGAL DIGITAL PRODUCTS
# Python 3.10+
#
# Install:
#   pip install python-telegram-bot
#
# Set environment variables:
#   BOT_TOKEN="8738576455:AAHWdiqXBAgbhWhLRnRrZyLrfrJLR4WbF94"
#   ADMIN_ID="8738576455"
#   SUPPORT_USERNAME="@YourSupportUsername"
#
# The welcome message is intentionally left EMPTY so you can add your own.
# Eight editable category buttons are provided below.
# Replace ONLY the category names/prices with legal products/content.

import json
import os
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("8738576455:AAHWdiqXBAgbhWhLRnRrZyLrfrJLR4WbF94", "")
ADMIN_ID = int(os.getenv("8999416691", "0"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@VIDEO_GROUP_PURCHASE")

DATA_FILE = Path("store_data.json")

# ============================================================
# WELCOME MESSAGE
# ============================================================
# Put your own welcome message between the triple quotes.
WELCOME_MESSAGE = """
"""

OFFER_MESSAGE = (
    "🔥 NEW OFFER\n\n"
    "Tap /start to open the store and view the latest categories."
)

START_HELP_MESSAGE = (
    "👋 Please tap /start to open the store and view our latest offers."
)

# ============================================================
# 8 CATEGORY BUTTONS
# ============================================================
# These are intentionally generic/legal placeholders.
# Replace name + price with your own LEGAL products.
CATEGORIES = {
    "cat1": {"name": "📚 PREMIUM COLLECTION 01", "price": 129},
    "cat2": {"name": "🎨 PREMIUM COLLECTION 02", "price": 49},
    "cat3": {"name": "💻 PREMIUM COLLECTION 03", "price": 70},
    "cat4": {"name": "🎓 PREMIUM COLLECTION 04", "price": 40},
    "cat5": {"name": "💎 PREMIUM COLLECTION 05", "price": 149},
    "cat6": {"name": "🔥 PREMIUM COLLECTION 06", "price": 199},
    "cat7": {"name": "⚡ PREMIUM COLLECTION 07", "price": 249},
    "cat8": {"name": "👑 PREMIUM COLLECTION 08", "price": 299},
}

# Telegram button styles. If the installed library/client does not
# support styles, the helper below automatically falls back to normal buttons.
BUTTON_STYLES = {
    "cat1": "primary",
    "cat2": "success",
    "cat3": "danger",
    "cat4": "secondary",
    "cat5": "primary",
    "cat6": "success",
    "cat7": "danger",
    "cat8": "secondary",
}

# ============================================================
# DATA
# ============================================================

def load_data():
    if not DATA_FILE.exists():
        return {
            "users": [],
            "demo_videos": [],
            "videos": {key: [] for key in CATEGORIES},
        }

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    data.setdefault("users", [])
    data.setdefault("demo_videos", [])
    data.setdefault("videos", {})

    for key in CATEGORIES:
        data["videos"].setdefault(key, [])

    return data


data = load_data()


def save_data():
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_admin(update: Update) -> bool:
    return bool(
        update.effective_user
        and update.effective_user.id == ADMIN_ID
    )


def add_user(user_id: int):
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data()


def support_url() -> str:
    return "https://t.me/" + SUPPORT_USERNAME.lstrip("@")


# ============================================================
# BUTTON HELPERS
# ============================================================

def styled_button(text: str, callback_data: str, style: str):
    try:
        return InlineKeyboardButton(
            text=text,
            callback_data=callback_data,
            style=style,
        )
    except TypeError:
        return InlineKeyboardButton(
            text=text,
            callback_data=callback_data,
        )


def category_keyboard():
    keys = list(CATEGORIES.keys())
    rows = []

    # 8 category buttons = 2 buttons per row.
    for i in range(0, len(keys), 2):
        row = []

        for key in keys[i:i + 2]:
            cat = CATEGORIES[key]

            row.append(
                styled_button(
                    f"{cat['name']} • ₹{cat['price']}",
                    f"category:{key}",
                    BUTTON_STYLES[key],
                )
            )

        rows.append(row)

    rows.append([
        InlineKeyboardButton(
            "🎁 LATEST OFFER",
            callback_data="offer",
        ),
        InlineKeyboardButton(
            "💬 SUPPORT",
            url=support_url(),
        ),
    ])

    return InlineKeyboardMarkup(rows)


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    add_user(update.effective_user.id)

    # Optional offer message.
    await update.message.reply_text(OFFER_MESSAGE)

    # Send up to 5 saved demo videos, one by one.
    for file_id in data["demo_videos"][:5]:
        try:
            await update.message.reply_video(video=file_id)
        except Exception:
            pass

    # Your custom welcome message.
    # It is blank by default.
    if WELCOME_MESSAGE.strip():
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=category_keyboard(),
        )
    else:
        await update.message.reply_text(
            "👇 CHOOSE A CATEGORY",
            reply_markup=category_keyboard(),
        )


# ============================================================
# CATEGORY DETAILS
# ============================================================

async def category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    key = query.data.split(":", 1)[1]
    cat = CATEGORIES.get(key)

    if not cat:
        return

    count = len(data["videos"].get(key, []))

    text = (
        f"{cat['name']}\n\n"
        f"💰 Price: ₹{cat['price']}\n"
        f"📦 Available files: {count}\n"
        f"⚡ Fast delivery\n"
        f"🔐 Secure service\n\n"
        "👇 Choose an option:"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📂 VIEW AVAILABLE • {count}",
                callback_data=f"videos:{key}",
            )
        ],
        [
            InlineKeyboardButton(
                "💬 SUPPORT",
                url=support_url(),
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ BACK",
                callback_data="home",
            )
        ],
    ])

    await query.message.reply_text(
        text,
        reply_markup=keyboard,
    )


async def videos_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    key = query.data.split(":", 1)[1]
    videos = data["videos"].get(key, [])

    if not videos:
        await query.message.reply_text(
            "📭 No files are available in this category yet."
        )
        return

    # Saved Telegram file_ids are reused.
    for file_id in videos:
        try:
            await query.message.reply_video(video=file_id)
        except Exception:
            pass


async def home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if WELCOME_MESSAGE.strip():
        await query.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=category_keyboard(),
        )
    else:
        await query.message.reply_text(
            "👇 CHOOSE A CATEGORY",
            reply_markup=category_keyboard(),
        )


async def offer_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        OFFER_MESSAGE,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🛍️ VIEW CATEGORIES",
                    callback_data="home",
                )
            ]
        ]),
    )


# ============================================================
# ADMIN: PERMANENT CATEGORY VIDEO STORAGE
# ============================================================

async def addvideo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update):
        return

    context.user_data["adding_video"] = True
    context.user_data.pop("pending_video", None)

    await update.message.reply_text(
        "🎬 Send the legal product/demo video now.\n\n"
        "After receiving it, select the category where it should be saved."
    )


async def handle_admin_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update):
        return

    if context.user_data.get("adding_demo"):
        if not update.message.video:
            return

        if len(data["demo_videos"]) >= 5:
            await update.message.reply_text(
                "⚠️ Maximum 5 demo videos are already saved. Use /done."
            )
            return

        data["demo_videos"].append(update.message.video.file_id)
        save_data()

        await update.message.reply_text(
            f"✅ Demo video saved "
            f"({len(data['demo_videos'])}/5).\n"
            "Send another video or /done."
        )
        return

    if not context.user_data.get("adding_video"):
        return

    if not update.message.video:
        return

    context.user_data["pending_video"] = update.message.video.file_id
    context.user_data["adding_video"] = False

    keys = list(CATEGORIES.keys())
    rows = []

    for i in range(0, len(keys), 2):
        row = []

        for key in keys[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    CATEGORIES[key]["name"],
                    callback_data=f"savevideo:{key}",
                )
            )

        rows.append(row)

    await update.message.reply_text(
        "✅ Video received.\n\n"
        "Choose a category to permanently save it:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def save_video_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    key = query.data.split(":", 1)[1]
    file_id = context.user_data.get("pending_video")

    if not file_id or key not in CATEGORIES:
        await query.message.reply_text(
            "❌ Session expired. Please use /addvideo again."
        )
        return

    data["videos"][key].append(file_id)
    save_data()

    context.user_data.pop("pending_video", None)

    await query.message.reply_text(
        "✅ Video permanently saved.\n\n"
        f"Category: {CATEGORIES[key]['name']}\n"
        f"Total saved: {len(data['videos'][key])}"
    )


# ============================================================
# ADMIN: DEMO SETUP
# ============================================================

async def setdemo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update):
        return

    data["demo_videos"] = []
    save_data()

    context.user_data["adding_demo"] = True

    await update.message.reply_text(
        "🎬 Demo setup started.\n\n"
        "Send up to 5 legal demo videos, one by one.\n"
        "Send /done when finished."
    )


async def done(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update):
        return

    context.user_data["adding_demo"] = False

    await update.message.reply_text(
        f"✅ Demo setup finished.\n"
        f"Saved: {len(data['demo_videos'])}/5"
    )


# ============================================================
# ADMIN: BROADCAST
# ============================================================

async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update):
        return

    context.user_data["broadcast_mode"] = True

    await update.message.reply_text(
        "📢 Send the broadcast now.\n\n"
        "Supported: text, photo, or video."
    )


async def handle_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update):
        return

    if not context.user_data.get("broadcast_mode"):
        return

    context.user_data["broadcast_mode"] = False

    sent = 0
    failed = 0

    for user_id in list(data["users"]):
        try:
            if update.message.text:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=update.message.text,
                )

            elif update.message.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=update.message.photo[-1].file_id,
                    caption=update.message.caption or "",
                )

            elif update.message.video:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=update.message.video.file_id,
                    caption=update.message.caption or "",
                )

            else:
                failed += 1
                continue

            sent += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast finished.\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )


# ============================================================
# UNKNOWN TEXT
# ============================================================

async def unknown_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.effective_user:
        return

    if is_admin(update) and (
        context.user_data.get("adding_video")
        or context.user_data.get("adding_demo")
        or context.user_data.get("broadcast_mode")
    ):
        return

    await update.message.reply_text(START_HELP_MESSAGE)


# ============================================================
# MAIN
# ============================================================

def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Set the BOT_TOKEN environment variable."
        )

    if not ADMIN_ID:
        raise RuntimeError(
            "ADMIN_ID is missing. Set the ADMIN_ID environment variable."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addvideo", addvideo))
    app.add_handler(CommandHandler("setdemo", setdemo))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(
        CallbackQueryHandler(
            category_callback,
            pattern=r"^category:",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            videos_callback,
            pattern=r"^videos:",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            save_video_callback,
            pattern=r"^savevideo:",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            home_callback,
            pattern=r"^home$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            offer_callback,
            pattern=r"^offer$",
        )
    )

    # Admin video handler.
    app.add_handler(
        MessageHandler(
            filters.VIDEO & filters.User(ADMIN_ID),
            handle_admin_video,
        )
    )

    # Admin broadcast handler.
    app.add_handler(
        MessageHandler(
            (
                filters.TEXT
                | filters.PHOTO
                | filters.VIDEO
            ) & filters.User(ADMIN_ID),
            handle_broadcast,
        )
    )

    # Unknown user text.
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            unknown_text,
        )
    )

    print("Premium Store Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
