# READY-TO-RUN TELEGRAM DIGITAL STORE BOT
# Legal digital products only.
# Python 3.10+
#
# Railway files:
#   premium_store_bot_fixed.py
#   requirements.txt
#   Procfile
#
# Environment variables:
#   BOT_TOKEN
#   ADMIN_ID
#   SUPPORT_USERNAME (optional)

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    JobQueue,
)

TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "").strip()
DATA_FILE = Path(os.getenv("DATA_FILE", "store_data.json"))

OFFER_MESSAGE = (
    "🔥 <b>NEW PREMIUM OFFER</b>\n\n"
    "Tap /start to open the store and explore the latest collections."
)
START_HELP_MESSAGE = "👋 Please tap /start to open the store and view our latest offers."

# Claim reminder settings
REMINDER_INTERVAL = 300          # 5 minutes (in seconds)
MAX_REMINDERS = 6                # max 6 reminders (30 minutes total)
CLAIM_TEXT = (
    "🔥 <b>Special Offer Still Available!</b>\n\n"
    "आपने अभी तक ऑफर क्लेम नहीं किया।\n"
    "अभी क्लिक करें और प्रीमियम कलेक्शन देखें 👇"
)

CATEGORIES = {
    "cat1": {"name": "📚 PREMIUM COLLECTION 01", "price": 129, "description": "Premium digital collection."},
    "cat2": {"name": "🎨 PREMIUM COLLECTION 02", "price": 49,  "description": "Premium digital collection."},
    "cat3": {"name": "💻 PREMIUM COLLECTION 03", "price": 70,  "description": "Premium digital collection."},
    "cat4": {"name": "🎓 PREMIUM COLLECTION 04", "price": 40,  "description": "Premium digital collection."},
    "cat5": {"name": "💎 PREMIUM COLLECTION 05", "price": 149, "description": "Premium digital collection."},
    "cat6": {"name": "🔥 PREMIUM COLLECTION 06", "price": 199, "description": "Premium digital collection."},
    "cat7": {"name": "⚡ PREMIUM COLLECTION 07", "price": 249, "description": "Premium digital collection."},
    "cat8": {"name": "👑 PREMIUM COLLECTION 08", "price": 299, "description": "Premium digital collection."},
}

BUTTON_STYLES = {
    "cat1": "primary", "cat2": "success", "cat3": "danger", "cat4": "primary",
    "cat5": "success", "cat6": "danger", "cat7": "primary", "cat8": "success",
}


def default_data():
    return {
        "users": [],
        "setup_complete": False,
        "start_videos": [],
        "welcome_message": "",
        "videos": {key: [] for key in CATEGORIES},
        "categories": {key: dict(value) for key, value in CATEGORIES.items()},
        "user_status": {},          # user_id -> {"claimed": bool, "reminders_sent": int, "last_start": str}
    }


def load_data():
    base = default_data()
    if not DATA_FILE.exists():
        return base
    try:
        saved = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(saved, dict):
            return base
    except Exception:
        return base

    base.update({k: v for k, v in saved.items() if k in base})
    base["users"] = list(dict.fromkeys(base.get("users", [])))
    base["start_videos"] = list(base.get("start_videos", []))
    base["welcome_message"] = str(base.get("welcome_message", ""))
    base["videos"] = base.get("videos", {}) if isinstance(base.get("videos"), dict) else {}
    base["categories"] = base.get("categories", {}) if isinstance(base.get("categories"), dict) else {}
    base["user_status"] = base.get("user_status", {}) if isinstance(base.get("user_status"), dict) else {}

    for key, default_cat in CATEGORIES.items():
        saved_cat = base["categories"].get(key, {})
        if not isinstance(saved_cat, dict):
            saved_cat = {}
        merged = dict(default_cat)
        merged.update(saved_cat)
        base["categories"][key] = merged
        base["videos"].setdefault(key, [])

    return base


data = load_data()


def save_data():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_FILE)


def is_admin(update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id == ADMIN_ID)


def add_user(user_id: int):
    if user_id not in data["users"]:
        data["users"].append(user_id)
    # reset status on every start
    data["user_status"][str(user_id)] = {
        "claimed": False,
        "reminders_sent": 0,
        "last_start": datetime.utcnow().isoformat(),
    }
    save_data()


def mark_claimed(user_id: int):
    uid = str(user_id)
    if uid not in data["user_status"]:
        data["user_status"][uid] = {"claimed": True, "reminders_sent": 0, "last_start": datetime.utcnow().isoformat()}
    else:
        data["user_status"][uid]["claimed"] = True
    save_data()


def support_url() -> Optional[str]:
    if not SUPPORT_USERNAME:
        return None
    return "https://t.me/" + SUPPORT_USERNAME.lstrip("@")


def styled_button(text, callback_data=None, style="primary", url=None):
    kwargs = {"text": text}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    try:
        return InlineKeyboardButton(**kwargs, style=style)
    except TypeError:
        return InlineKeyboardButton(**kwargs)


def category_keyboard():
    keys = list(CATEGORIES.keys())
    rows = []
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i + 2]:
            cat = data["categories"][key]
            row.append(styled_button(
                f"{cat['name']}  •  ₹{cat['price']}",
                f"category:{key}",
                BUTTON_STYLES[key],
            ))
        rows.append(row)

    support = support_url()
    bottom = [styled_button("🎁  LATEST OFFER", "offer", "primary")]
    if support:
        bottom.append(styled_button("💬  SUPPORT", url=support, style="success"))
    rows.append(bottom)
    return InlineKeyboardMarkup(rows)


async def send_store(update: Update):
    message = update.effective_message
    if not message:
        return

    await message.reply_text(OFFER_MESSAGE, parse_mode="HTML")

    for file_id in data["start_videos"][:6]:
        try:
            await message.reply_video(video=file_id)
        except Exception:
            pass

    welcome = data["welcome_message"].strip()
    if welcome:
        await message.reply_text(welcome, reply_markup=category_keyboard(), parse_mode="HTML")
    else:
        await message.reply_text(
            "👇 <b>CHOOSE A CATEGORY</b>",
            reply_markup=category_keyboard(),
            parse_mode="HTML"
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    add_user(user_id)

    # Schedule claim reminders
    job_name = f"reminder_{user_id}"
    # remove old job if exists
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        send_claim_reminder,
        interval=REMINDER_INTERVAL,
        first=REMINDER_INTERVAL,
        data={"user_id": user_id},
        name=job_name,
        job_kwargs={"misfire_grace_time": 60},
    )

    await send_store(update)


async def send_claim_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.data["user_id"]
    uid = str(user_id)

    status = data["user_status"].get(uid, {})
    if status.get("claimed"):
        job.schedule_removal()
        return

    if status.get("reminders_sent", 0) >= MAX_REMINDERS:
        job.schedule_removal()
        return

    keyboard = InlineKeyboardMarkup([
        [styled_button("🎁  CLAIM NOW", "claim_now", "success")]
    ])

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=CLAIM_TEXT,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        data["user_status"][uid]["reminders_sent"] = status.get("reminders_sent", 0) + 1
        save_data()
    except Exception:
        # user blocked the bot or chat not found
        job.schedule_removal()


async def claim_now_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🎁 Opening your offer...")
    user_id = query.from_user.id
    mark_claimed(user_id)

    # stop further reminders
    job_name = f"reminder_{user_id}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    # open the store
    await send_store(update)


# ----------------------------- Category display -----------------------------

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    cat = data["categories"].get(key)
    if not cat:
        return

    # user interacted → mark claimed so reminders stop
    mark_claimed(query.from_user.id)
    job_name = f"reminder_{query.from_user.id}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    count = len(data["videos"].get(key, []))
    text = (
        f"<b>{cat['name']}</b>\n\n"
        f"📝 {cat['description']}\n\n"
        f"💰 <b>Price:</b> ₹{cat['price']}\n"
        f"📦 <b>Demo files:</b> {count}\n\n"
        "👇 Choose an option:"
    )

    rows = [[styled_button(f"📂  VIEW DEMO  •  {count}", f"videos:{key}", "primary")]]
    support = support_url()
    if support:
        rows.append([styled_button("💬  SUPPORT", url=support, style="success")])
    rows.append([styled_button("⬅️  BACK", "home", "secondary")])
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")


async def videos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    videos = data["videos"].get(key, [])
    if not videos:
        await query.message.reply_text("📭 No demo files are available in this category yet.")
        return
    for file_id in videos[:5]:
        try:
            await query.message.reply_video(video=file_id)
        except Exception:
            pass


async def home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    welcome = data["welcome_message"].strip()
    await query.message.reply_text(
        welcome or "👇 <b>CHOOSE A CATEGORY</b>",
        reply_markup=category_keyboard(),
        parse_mode="HTML"
    )


async def offer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        OFFER_MESSAGE,
        reply_markup=InlineKeyboardMarkup([
            [styled_button("🛍️  VIEW CATEGORIES", "home", "primary")]
        ]),
        parse_mode="HTML"
    )


# ----------------------------- Admin panel -----------------------------

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [styled_button("🎬  SET START VIDEOS (max 6)", "admin:startvideos", "primary")],
        [styled_button("📝  SET WELCOME MESSAGE", "admin:welcome", "success")],
        [styled_button("📂  CATEGORY SETUP", "admin:categories", "danger")],
        [styled_button("🚀  COMPLETE SETUP", "admin:complete", "primary")],
        [styled_button("📢  BROADCAST", "admin:broadcast", "success")],
    ])


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    context.user_data.clear()
    await update.message.reply_text(
        "👑 <b>ADMIN PANEL</b>\n\nChoose an option:",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )


def category_admin_keyboard():
    rows = []
    keys = list(CATEGORIES.keys())
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i + 2]:
            cat = data["categories"][key]
            row.append(styled_button(
                f"{key.upper()} • {cat['name']}",
                f"admincat:{key}",
                BUTTON_STYLES[key]
            ))
        rows.append(row)
    rows.append([styled_button("⬅️  ADMIN PANEL", "admin:panel", "secondary")])
    return InlineKeyboardMarkup(rows)


def category_edit_keyboard(key):
    return InlineKeyboardMarkup([
        [styled_button("✏️  CHANGE CATEGORY NAME", f"editname:{key}", "primary")],
        [styled_button("📝  CHANGE DESCRIPTION", f"editdesc:{key}", "success")],
        [styled_button("💰  CHANGE PRICE", f"editprice:{key}", "danger")],
        [styled_button("🎬  ADD DEMO VIDEOS (max 5)", f"addcatvideos:{key}", "primary")],
        [styled_button("⬅️  CATEGORY LIST", "admin:categories", "secondary")],
    ])


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    action = query.data.split(":", 1)[1]
    context.user_data.pop("mode", None)
    context.user_data.pop("category", None)

    if action == "panel":
        await query.message.reply_text(
            "👑 <b>ADMIN PANEL</b>",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )
    elif action == "startvideos":
        data["start_videos"] = []
        save_data()
        context.user_data["mode"] = "start_videos"
        await query.message.reply_text(
            "🎬 Send <b>1–6 start videos</b>, one by one.\n\nSend /done when finished.",
            parse_mode="HTML"
        )
    elif action == "welcome":
        context.user_data["mode"] = "welcome"
        await query.message.reply_text(
            "📝 Send the <b>welcome message</b> now.\n\nYou can use HTML (bold, italic etc).",
            parse_mode="HTML"
        )
    elif action == "categories":
        await query.message.reply_text(
            "📂 Select the category you want to edit:",
            reply_markup=category_admin_keyboard()
        )
    elif action == "complete":
        data["setup_complete"] = True
        save_data()
        await query.message.reply_text(
            "✅ <b>Setup completed!</b>\n\n"
            "From now on /start opens the store normally.\n"
            "Use /admin anytime for settings.",
            parse_mode="HTML"
        )
    elif action == "broadcast":
        context.user_data["mode"] = "broadcast"
        await query.message.reply_text(
            "📢 Send the broadcast text / photo / video now.\n\nSend /cancel to cancel."
        )


async def admin_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    key = query.data.split(":", 1)[1]
    if key not in CATEGORIES:
        return
    context.user_data["category"] = key
    cat = data["categories"][key]
    await query.message.reply_text(
        f"<b>{key.upper()}</b>\n\n"
        f"Name: {cat['name']}\n"
        f"Price: ₹{cat['price']}\n"
        f"Description: {cat['description']}\n"
        f"Demo videos: {len(data['videos'][key])}",
        reply_markup=category_edit_keyboard(key),
        parse_mode="HTML"
    )


async def edit_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    action, key = query.data.split(":", 1)
    if key not in CATEGORIES:
        return
    context.user_data["category"] = key

    if action == "editname":
        context.user_data["mode"] = "category_name"
        await query.message.reply_text(f"✏️ Send the new name for <b>{key.upper()}</b>.", parse_mode="HTML")
    elif action == "editdesc":
        context.user_data["mode"] = "category_description"
        await query.message.reply_text(f"📝 Send the new description for <b>{key.upper()}</b>.", parse_mode="HTML")
    elif action == "editprice":
        context.user_data["mode"] = "category_price"
        await query.message.reply_text(f"💰 Send the new price (numbers only) for <b>{key.upper()}</b>.", parse_mode="HTML")
    elif action == "addcatvideos":
        context.user_data["mode"] = "category_videos"
        await query.message.reply_text(
            f"🎬 Send up to <b>5 demo videos</b> for {key.upper()}, one by one.\n\nSend /done when finished.",
            parse_mode="HTML"
        )


# ----------------------------- Admin message router -----------------------------

async def admin_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update) or not update.message:
        return
    mode = context.user_data.get("mode")
    if not mode:
        return

    msg = update.message

    if msg.text and msg.text.strip().lower() == "/cancel":
        context.user_data.clear()
        await msg.reply_text("❌ Cancelled. Use /admin to continue.")
        return

    if mode == "welcome":
        if not msg.text:
            await msg.reply_text("📝 Please send the welcome message as text.")
            return
        data["welcome_message"] = msg.text
        save_data()
        context.user_data["mode"] = None
        await msg.reply_text("✅ Welcome message saved. Use /admin to continue.")
        return

    if mode == "start_videos":
        if not msg.video:
            await msg.reply_text("🎬 Please send a video.")
            return
        if len(data["start_videos"]) >= 6:
            await msg.reply_text("⚠️ 6 start videos are already saved. Send /done.")
            return
        data["start_videos"].append(msg.video.file_id)
        save_data()
        await msg.reply_text(f"✅ Start video saved: <b>{len(data['start_videos'])}/6</b>\nSend another or /done.", parse_mode="HTML")
        return

    if mode == "category_videos":
        key = context.user_data.get("category")
        if key not in CATEGORIES:
            context.user_data.clear()
            await msg.reply_text("❌ Category session expired. Use /admin again.")
            return
        if not msg.video:
            await msg.reply_text("🎬 Please send a video.")
            return
        if len(data["videos"][key]) >= 5:
            await msg.reply_text("⚠️ 5 demo videos are already saved for this category. Send /done.")
            return
        data["videos"][key].append(msg.video.file_id)
        save_data()
        await msg.reply_text(
            f"✅ Video saved to <b>{key.upper()}</b>: {len(data['videos'][key])}/5\nSend another or /done.",
            parse_mode="HTML"
        )
        return

    if mode == "category_name":
        key = context.user_data.get("category")
        if key not in CATEGORIES or not msg.text:
            await msg.reply_text("📝 Send a text name.")
            return
        data["categories"][key]["name"] = msg.text.strip()
        save_data()
        context.user_data.clear()
        await msg.reply_text(
            f"✅ <b>{key.upper()}</b> name updated.\nNew name: {data['categories'][key]['name']}",
            reply_markup=category_admin_keyboard(),
            parse_mode="HTML"
        )
        return

    if mode == "category_description":
        key = context.user_data.get("category")
        if key not in CATEGORIES or not msg.text:
            await msg.reply_text("📝 Send a text description.")
            return
        data["categories"][key]["description"] = msg.text.strip()
        save_data()
        context.user_data.clear()
        await msg.reply_text(
            f"✅ <b>{key.upper()}</b> description updated.",
            reply_markup=category_admin_keyboard(),
            parse_mode="HTML"
        )
        return

    if mode == "category_price":
        key = context.user_data.get("category")
        if key not in CATEGORIES or not msg.text:
            await msg.reply_text("💰 Send the price as numbers only, e.g. 129")
            return
        try:
            price = int(msg.text.strip())
            if price < 0:
                raise ValueError
        except ValueError:
            await msg.reply_text("❌ Invalid price. Send numbers only, e.g. 129")
            return
        data["categories"][key]["price"] = price
        save_data()
        context.user_data.clear()
        await msg.reply_text(
            f"✅ <b>{key.upper()}</b> price updated to ₹{price}.",
            reply_markup=category_admin_keyboard(),
            parse_mode="HTML"
        )
        return

    if mode == "broadcast":
        context.user_data.clear()
        sent = failed = 0
        for user_id in list(data["users"]):
            try:
                if msg.text:
                    await context.bot.send_message(user_id, msg.text, parse_mode="HTML")
                elif msg.photo:
                    await context.bot.send_photo(user_id, msg.photo[-1].file_id, caption=msg.caption or "")
                elif msg.video:
                    await context.bot.send_video(user_id, msg.video.file_id, caption=msg.caption or "")
                else:
                    failed += 1
                    continue
                sent += 1
            except Exception:
                failed += 1
        await msg.reply_text(f"📢 Broadcast finished.\n\n✅ Sent: {sent}\n❌ Failed: {failed}")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    mode = context.user_data.get("mode")
    if mode in {"start_videos", "category_videos"}:
        saved = len(data["start_videos"]) if mode == "start_videos" else len(data["videos"].get(context.user_data.get("category"), []))
        context.user_data.clear()
        await update.message.reply_text(f"✅ Video setup finished. Saved: <b>{saved}</b>", parse_mode="HTML")
    elif mode == "welcome":
        context.user_data.clear()
        await update.message.reply_text("✅ Welcome setup finished.")
    else:
        await update.message.reply_text("Nothing is currently waiting for /done.")


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if is_admin(update) and context.user_data.get("mode"):
        await admin_message_router(update, context)
        return
    await update.message.reply_text(START_HELP_MESSAGE)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Add BOT_TOKEN in Railway Variables.")
    if not ADMIN_ID:
        raise RuntimeError("ADMIN_ID is missing. Add ADMIN_ID in Railway Variables.")

    app = ApplicationBuilder().token(TOKEN).build()

    # JobQueue is available by default in recent PTB
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("done", done))

    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin:"))
    app.add_handler(CallbackQueryHandler(admin_category_callback, pattern=r"^admincat:"))
    app.add_handler(CallbackQueryHandler(edit_category_callback, pattern=r"^(editname|editdesc|editprice|addcatvideos):"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^category:"))
    app.add_handler(CallbackQueryHandler(videos_callback, pattern=r"^videos:"))
    app.add_handler(CallbackQueryHandler(home_callback, pattern=r"^home$"))
    app.add_handler(CallbackQueryHandler(offer_callback, pattern=r"^offer$"))
    app.add_handler(CallbackQueryHandler(claim_now_callback, pattern=r"^claim_now$"))

    app.add_handler(MessageHandler(filters.ALL & filters.User(ADMIN_ID), admin_message_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    print("Premium Store Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
