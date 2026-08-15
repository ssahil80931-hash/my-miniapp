# ============================================================
# PREMIUM DIGITAL STORE TELEGRAM BOT
# Python 3.10+
#
# Install:
# pip install python-telegram-bot qrcode[pil]
#
# Railway Procfile:
# worker: python bot.py
# ============================================================

import json
from pathlib import Path
from io import BytesIO

import qrcode

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIG
# ============================================================

TOKEN = "PASTE_YOUR_NEW_BOT_TOKEN_HERE"

ADMIN_ID = 8999416691

SUPPORT_USERNAME = "@VIDEO_GROUP_PURCHASE"

UPI_ID = "YOUR_UPI_ID@upi"
UPI_NAME = "YOUR STORE NAME"

DATA_FILE = Path("store_data.json")


# ============================================================
# WELCOME MESSAGE
# ============================================================
# यहाँ अपना welcome message डाल सकते हो.
# खाली छोड़ोगे तो default message आएगा.

WELCOME_MESSAGE = ""


# ============================================================
# 8 CATEGORIES
#
# सिर्फ name और price बदलना है.
# Description अपने-आप generate होगी.
# ============================================================

CATEGORIES = {

    "cat1": {
        "name": "CATEGORY 1",
        "price": 129,
        "access_link": "https://t.me/YOUR_CHANNEL_1",
        "style": "primary",
    },

    "cat2": {
        "name": "CATEGORY 2",
        "price": 49,
        "access_link": "https://t.me/YOUR_CHANNEL_2",
        "style": "success",
    },

    "cat3": {
        "name": "CATEGORY 3",
        "price": 70,
        "access_link": "https://t.me/YOUR_CHANNEL_3",
        "style": "danger",
    },

    "cat4": {
        "name": "CATEGORY 4",
        "price": 40,
        "access_link": "https://t.me/YOUR_CHANNEL_4",
        "style": None,
    },

    "cat5": {
        "name": "CATEGORY 5",
        "price": 149,
        "access_link": "https://t.me/YOUR_CHANNEL_5",
        "style": "primary",
    },

    "cat6": {
        "name": "CATEGORY 6",
        "price": 199,
        "access_link": "https://t.me/YOUR_CHANNEL_6",
        "style": "success",
    },

    "cat7": {
        "name": "CATEGORY 7",
        "price": 249,
        "access_link": "https://t.me/YOUR_CHANNEL_7",
        "style": "danger",
    },

    "cat8": {
        "name": "CATEGORY 8",
        "price": 299,
        "access_link": "https://t.me/YOUR_CHANNEL_8",
        "style": None,
    },
}


# ============================================================
# DEFAULT TEXT
# ============================================================

NEW_OFFER_TEXT = (
    "🔥 NEW OFFER\n\n"
    "Tap /start to open the store and view the latest categories."
)

START_HELP_TEXT = (
    "👋 Please tap /start to open the store "
    "and view the latest offers."
)


# ============================================================
# DATABASE
# ============================================================

def create_default_data():

    return {
        "users": [],
        "start_videos": [],
        "welcome_message": "",
        "category_videos": {
            key: []
            for key in CATEGORIES
        },
        "payments": {},
        "setup_complete": False,
    }


def load_data():

    if not DATA_FILE.exists():
        return create_default_data()

    try:

        data = json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return create_default_data()

    default = create_default_data()

    for key, value in default.items():

        if key not in data:
            data[key] = value

    for key in CATEGORIES:

        data["category_videos"].setdefault(
            key,
            []
        )

    return data


data = load_data()


def save_data():

    DATA_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# ============================================================
# BASIC HELPERS
# ============================================================

def is_admin(update):

    return bool(
        update.effective_user
        and
        update.effective_user.id == ADMIN_ID
    )


def add_user(user_id):

    if user_id not in data["users"]:

        data["users"].append(user_id)

        save_data()


def support_url():

    return (
        "https://t.me/"
        + SUPPORT_USERNAME.lstrip("@")
    )


def button(
    text,
    callback_data=None,
    style=None,
    url=None
):

    kwargs = {
        "text": text
    }

    if callback_data:
        kwargs["callback_data"] = callback_data

    if url:
        kwargs["url"] = url

    if style:
        kwargs["style"] = style

    try:

        return InlineKeyboardButton(
            **kwargs
        )

    except TypeError:

        # Fallback for older python-telegram-bot
        kwargs.pop(
            "style",
            None
        )

        return InlineKeyboardButton(
            **kwargs
        )


# ============================================================
# AUTOMATIC CATEGORY DESCRIPTION
# ============================================================

def category_description(
    key
):

    cat = CATEGORIES[key]

    return (
        f"✨ {cat['name']}\n\n"
        f"💰 Price: ₹{cat['price']}\n"
        "📁 File Delivery\n"
        "⚡ Fast Delivery\n"
        "🔐 Secure Payment"
    )


# ============================================================
# USER CATEGORY BUTTONS
# ============================================================

def category_keyboard():

    keys = list(
        CATEGORIES.keys()
    )

    rows = []

    for i in range(
        0,
        len(keys),
        2
    ):

        row = []

        for key in keys[i:i + 2]:

            cat = CATEGORIES[key]

            row.append(
                button(
                    f"{cat['name']} • ₹{cat['price']}",
                    callback_data=f"category:{key}",
                    style=cat["style"]
                )
            )

        rows.append(row)

    rows.append([
        button(
            "🎁 NEW OFFER",
            callback_data="offer",
            style="primary"
        ),
        button(
            "💬 SUPPORT",
            url=support_url()
        )
    ])

    return InlineKeyboardMarkup(rows)


# ============================================================
# ADMIN CATEGORY BUTTONS
# ============================================================

def admin_category_keyboard():

    keys = list(
        CATEGORIES.keys()
    )

    rows = []

    for i in range(
        0,
        len(keys),
        2
    ):

        row = []

        for key in keys[i:i + 2]:

            cat = CATEGORIES[key]

            row.append(
                button(
                    cat["name"],
                    callback_data=f"admin_category:{key}",
                    style=cat["style"]
                )
            )

        rows.append(row)

    rows.append([
        button(
            "🚀 FINISH SETUP",
            callback_data="finish_setup",
            style="success"
        )
    ])

    return InlineKeyboardMarkup(rows)


# ============================================================
# QR GENERATOR
# ============================================================

def generate_qr(
    amount,
    category_name
):

    upi_url = (
        "upi://pay"
        f"?pa={UPI_ID}"
        f"&pn={UPI_NAME}"
        f"&am={amount}"
        "&cu=INR"
        f"&tn={category_name}"
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(
        upi_url
    )

    qr.make(
        fit=True
    )

    image = qr.make_image()

    output = BytesIO()

    image.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return output


# ============================================================
# /START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    # ADMIN
    if is_admin(update):

        await update.message.reply_text(
            "👑 ADMIN PANEL\n\n"
            "Choose an option:",
            reply_markup=InlineKeyboardMarkup([
                [
                    button(
                        "🎬 SET START VIDEOS",
                        callback_data="setup_start",
                        style="primary"
                    )
                ],
                [
                    button(
                        "📝 SET WELCOME MESSAGE",
                        callback_data="setup_welcome",
                        style="success"
                    )
                ],
                [
                    button(
                        "📂 SET CATEGORY VIDEOS",
                        callback_data="setup_categories",
                        style="danger"
                    )
                ],
                [
                    button(
                        "🚀 COMPLETE SETUP",
                        callback_data="finish_setup",
                        style="success"
                    )
                ]
            ])
        )

        return

    # USER
    add_user(
        update.effective_user.id
    )

    await update.message.reply_text(
        NEW_OFFER_TEXT
    )

    # 6 start videos
    for file_id in data["start_videos"][:6]:

        try:

            await update.message.reply_video(
                video=file_id
            )

        except Exception:
            pass

    # Welcome message
    if data["welcome_message"].strip():

        await update.message.reply_text(
            data["welcome_message"],
            reply_markup=category_keyboard()
        )

    else:

        await update.message.reply_text(
            "✨ WELCOME\n\n"
            "👇 CHOOSE YOUR CATEGORY",
            reply_markup=category_keyboard()
        )


# ============================================================
# CATEGORY CLICK
# ============================================================

async def category_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    key = query.data.split(
        ":",
        1
    )[1]

    if key not in CATEGORIES:
        return

    cat = CATEGORIES[key]

    videos = data[
        "category_videos"
    ].get(
        key,
        []
    )

    # Send 5 saved category videos
    for file_id in videos[:5]:

        try:

            await query.message.reply_video(
                video=file_id
            )

        except Exception:
            pass

    details = category_description(
        key
    )

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "💳 I HAVE PAID",
                callback_data=f"paid:{key}",
                style="success"
            )
        ],
        [
            button(
                "💬 SUPPORT",
                url=support_url()
            )
        ],
        [
            button(
                "⬅️ BACK",
                callback_data="home"
            )
        ]
    ])

    qr = generate_qr(
        cat["price"],
        cat["name"]
    )

    caption = (
        f"{details}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💳 UPI: {UPI_ID}\n"
        f"👤 Name: {UPI_NAME}\n"
        f"💵 Amount: ₹{cat['price']}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Scan the QR to pay."
    )

    await query.message.reply_photo(
        photo=qr,
        caption=caption,
        reply_markup=keyboard
    )


# ============================================================
# HOME
# ============================================================

async def home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    welcome = data["welcome_message"]

    if welcome.strip():

        await query.message.reply_text(
            welcome,
            reply_markup=category_keyboard()
        )

    else:

        await query.message.reply_text(
            "👇 CHOOSE YOUR CATEGORY",
            reply_markup=category_keyboard()
        )


# ============================================================
# OFFER
# ============================================================

async def offer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    await query.message.reply_text(
        NEW_OFFER_TEXT,
        reply_markup=InlineKeyboardMarkup([
            [
                button(
                    "🛍️ VIEW CATEGORIES",
                    callback_data="home",
                    style="primary"
                )
            ]
        ])
    )


# ============================================================
# I HAVE PAID
# ============================================================

async def paid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    key = query.data.split(
        ":",
        1
    )[1]

    if key not in CATEGORIES:
        return

    context.user_data[
        "payment_category"
    ] = key

    await query.message.reply_text(
        "📸 PAYMENT PROOF\n\n"
        "Please send your payment screenshot "
        "as a photo."
    )


# ============================================================
# PAYMENT SCREENSHOT
# ============================================================

async def payment_screenshot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if is_admin(update):
        return

    key = context.user_data.get(
        "payment_category"
    )

    if not key:
        return

    if not update.message.photo:

        await update.message.reply_text(
            "📸 Please send the payment screenshot as a photo."
        )

        return

    photo = update.message.photo[-1]

    user = update.effective_user

    payment_id = (
        f"{user.id}_"
        f"{update.message.message_id}"
    )

    data["payments"][payment_id] = {
        "user_id": user.id,
        "category": key,
        "status": "pending"
    }

    save_data()

    cat = CATEGORIES[key]

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "✅ APPROVE",
                callback_data=f"approve:{payment_id}",
                style="success"
            ),
            button(
                "❌ REJECT",
                callback_data=f"reject:{payment_id}",
                style="danger"
            )
        ]
    ])

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption=(
            "💳 NEW PAYMENT PROOF\n\n"
            f"👤 User: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📦 Category: {cat['name']}\n"
            f"💰 Amount: ₹{cat['price']}\n\n"
            "Choose APPROVE or REJECT."
        ),
        reply_markup=keyboard
    )

    await update.message.reply_text(
        "✅ Payment proof received.\n\n"
        "⏳ Please wait for admin approval."
    )

    context.user_data.pop(
        "payment_category",
        None
    )


# ============================================================
# APPROVE
# ============================================================

async def approve(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    payment_id = query.data.split(
        ":",
        1
    )[1]

    payment = data["payments"].get(
        payment_id
    )

    if not payment:
        return

    if payment["status"] != "pending":
        return

    payment["status"] = "approved"

    save_data()

    key = payment["category"]

    cat = CATEGORIES[key]

    user_id = payment["user_id"]

    try:

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ PAYMENT APPROVED\n\n"
                f"📦 {cat['name']}\n"
                f"💰 ₹{cat['price']}\n\n"
                "🎉 Your access is ready."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    button(
                        "🔓 OPEN ACCESS",
                        url=cat["access_link"],
                        style="primary"
                    )
                ]
            ])
        )

    except Exception:
        pass

    await query.message.edit_caption(
        caption=(
            query.message.caption
            + "\n\n✅ APPROVED"
        )
    )


# ============================================================
# REJECT
# ============================================================

async def reject(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    payment_id = query.data.split(
        ":",
        1
    )[1]

    payment = data["payments"].get(
        payment_id
    )

    if not payment:
        return

    if payment["status"] != "pending":
        return

    payment["status"] = "rejected"

    save_data()

    try:

        await context.bot.send_message(
            chat_id=payment["user_id"],
            text=(
                "❌ PAYMENT PROOF REJECTED\n\n"
                "Please contact support if you believe "
                "this was a mistake."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    button(
                        "💬 SUPPORT",
                        url=support_url()
                    )
                ]
            ])
        )

    except Exception:
        pass

    await query.message.edit_caption(
        caption=(
            query.message.caption
            + "\n\n❌ REJECTED"
        )
    )


# ============================================================
# ADMIN: START VIDEOS
# ============================================================

async def setup_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data["start_videos"] = []

    save_data()

    context.user_data[
        "setup_mode"
    ] = "start_videos"

    await query.message.reply_text(
        "🎬 START VIDEO SETUP\n\n"
        "Send up to 6 videos one by one.\n\n"
        "When finished, send /done."
    )


# ============================================================
# ADMIN: WELCOME
# ============================================================

async def setup_welcome(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data[
        "setup_mode"
    ] = "welcome"

    await query.message.reply_text(
        "📝 WELCOME MESSAGE\n\n"
        "Send your welcome message now.\n\n"
        "After sending it, use /done."
    )


# ============================================================
# ADMIN: CATEGORY SETUP
# ============================================================

async def setup_categories(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data[
        "setup_mode"
    ] = "choose_category"

    await query.message.reply_text(
        "📂 SELECT CATEGORY\n\n"
        "Choose a category to upload its videos:",
        reply_markup=admin_category_keyboard()
    )


# ============================================================
# ADMIN CATEGORY SELECT
# ============================================================

async def admin_category(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    key = query.data.split(
        ":",
        1
    )[1]

    context.user_data[
        "current_category"
    ] = key

    context.user_data[
        "setup_mode"
    ] = "category_videos"

    # Start fresh for this category
    data["category_videos"][key] = []

    save_data()

    cat = CATEGORIES[key]

    await query.message.reply_text(
        f"📂 {cat['name']}\n\n"
        "Send 4–5 videos one by one.\n"
        "They will be permanently saved.\n\n"
        "Send /done when finished."
    )


# ============================================================
# ADMIN VIDEO RECEIVER
# ============================================================

async def admin_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return

    if not update.message.video:
        return

    mode = context.user_data.get(
        "setup_mode"
    )

    file_id = update.message.video.file_id

    # START VIDEOS
    if mode == "start_videos":

        if len(
            data["start_videos"]
        ) >= 6:

            await update.message.reply_text(
                "⚠️ Maximum 6 start videos reached.\n"
                "Send /done."
            )

            return

        data["start_videos"].append(
            file_id
        )

        save_data()

        await update.message.reply_text(
            f"✅ Start video saved "
            f"({len(data['start_videos'])}/6).\n"
            "Send another video or /done."
        )

        return

    # CATEGORY VIDEOS
    if mode == "category_videos":

        key = context.user_data.get(
            "current_category"
        )

        if not key:
            return

        if len(
            data["category_videos"][key]
        ) >= 5:

            await update.message.reply_text(
                "⚠️ Maximum 5 videos reached.\n"
                "Send /done."
            )

            return

        data["category_videos"][key].append(
            file_id
        )

        save_data()

        await update.message.reply_text(
            f"✅ Video permanently saved "
            f"({len(data['category_videos'][key])}/5).\n"
            "Send another video or /done."
        )


# ============================================================
# ADMIN WELCOME TEXT
# ============================================================

async def admin_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return

    mode = context.user_data.get(
        "setup_mode"
    )

    if mode != "welcome":
        return

    data["welcome_message"] = (
        update.message.text
    )

    save_data()

    await update.message.reply_text(
        "✅ Welcome message saved.\n\n"
        "Now send /done."
    )


# ============================================================
# /DONE
# ============================================================

async def done(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return

    mode = context.user_data.get(
        "setup_mode"
    )

    # START
    if mode == "start_videos":

        context.user_data.pop(
            "setup_mode",
            None
        )

        await update.message.reply_text(
            "✅ Start videos completed.\n\n"
            f"Saved: {len(data['start_videos'])}/6\n\n"
            "Now set your Welcome Message.",
            reply_markup=InlineKeyboardMarkup([
                [
                    button(
                        "📝 SET WELCOME",
                        callback_data="setup_welcome",
                        style="success"
                    )
                ]
            ])
        )

        return

    # WELCOME
    if mode == "welcome":

        context.user_data.pop(
            "setup_mode",
            None
        )

        await update.message.reply_text(
            "✅ Welcome message completed.\n\n"
            "Now configure category videos.",
            reply_markup=InlineKeyboardMarkup([
                [
                    button(
                        "📂 SELECT CATEGORY",
                        callback_data="setup_categories",
                        style="primary"
                    )
                ]
            ])
        )

        return

    # CATEGORY
    if mode == "category_videos":

        key = context.user_data.get(
            "current_category"
        )

        count = 0

        if key:

            count = len(
                data["category_videos"][key]
            )

        context.user_data.pop(
            "current_category",
            None
        )

        context.user_data[
            "setup_mode"
        ] = "choose_category"

        await update.message.reply_text(
            f"✅ Category completed.\n"
            f"Videos saved: {count}\n\n"
            "Choose another category:",
            reply_markup=admin_category_keyboard()
        )

        return


# ============================================================
# FINISH SETUP
# ============================================================

async def finish_setup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data["setup_complete"] = True

    save_data()

    context.user_data.clear()

    await query.message.reply_text(
        "🚀 BOT IS LIVE\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Start videos\n"
        "✅ Welcome message\n"
        "✅ 8 categories\n"
        "✅ Category videos\n"
        "✅ QR payment\n"
        "✅ Payment proof\n"
        "✅ Approve / Reject\n"
        "✅ Access delivery\n"
        "━━━━━━━━━━━━━━━━━━"
    )


# ============================================================
# UNKNOWN USER TEXT
# ============================================================

async def unknown_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if is_admin(update):
        return

    await update.message.reply_text(
        START_HELP_TEXT
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if (
        not TOKEN
        or
        TOKEN == "PASTE_YOUR_NEW_BOT_TOKEN_HERE"
    ):

        raise RuntimeError(
            "Please put your new bot token in TOKEN."
        )

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    # -------------------------
    # Commands
    # -------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "done",
            done
        )
    )

    # -------------------------
    # User callbacks
    # -------------------------

    app.add_handler(
        CallbackQueryHandler(
            category_click,
            pattern=r"^category:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            paid,
            pattern=r"^paid:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            approve,
            pattern=r"^approve:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            reject,
            pattern=r"^reject:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            home,
            pattern=r"^home$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            offer,
            pattern=r"^offer$"
        )
    )

    # -------------------------
    # Admin setup
    # -------------------------

    app.add_handler(
        CallbackQueryHandler(
            setup_start,
            pattern=r"^setup_start$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            setup_welcome,
            pattern=r"^setup_welcome$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            setup_categories,
            pattern=r"^setup_categories$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_category,
            pattern=r"^admin_category:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            finish_setup,
            pattern=r"^finish_setup$"
        )
    )

    # -------------------------
    # Admin videos
    # -------------------------

    app.add_handler(
        MessageHandler(
            filters.VIDEO
            & filters.User(ADMIN_ID),
            admin_video
        )
    )

    # -------------------------
    # Payment screenshot
    # -------------------------

    app.add_handler(
        MessageHandler(
            filters.PHOTO
            & ~filters.User(ADMIN_ID),
            payment_screenshot
        )
    )

    # -------------------------
    # Admin welcome text
    # -------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.User(ADMIN_ID),
            admin_text
        )
    )

    # -------------------------
    # Unknown user text
    # -------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & ~filters.User(ADMIN_ID),
            unknown_text
        )
    )

    print(
        "🔥 PREMIUM DIGITAL STORE BOT RUNNING..."
    )

    app.run_polling()


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":
    main()