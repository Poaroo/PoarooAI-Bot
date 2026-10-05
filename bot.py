# -*- coding: utf-8 -*-
"""PoarooAI Bot | v1.0 AiSecuredByPoaroo4 | Design By Poaroo"""
import os
import sys
import json
import logging
from datetime import date
from io import BytesIO
from urllib.parse import quote

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("poaroo")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
OWNER_ID = int(os.environ.get("OWNER_ID", "6130352235") or "6130352235")
BOT_VERSION = "v1.0 AiSecuredByPoaroo4"

if not TELEGRAM_TOKEN:
    log.error("TELEGRAM_TOKEN missing")
    sys.exit(1)
if not GROQ_API_KEY:
    log.error("GROQ_API_KEY missing")
    sys.exit(1)

log.info(
    "Env OK token_len=%s groq_len=%s owner=%s",
    len(TELEGRAM_TOKEN),
    len(GROQ_API_KEY),
    OWNER_ID,
)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from openai import OpenAI

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

DATA_FILE = "bot_data.json"
COIN_FILE = "coin_data.json"

GRADE_NAMES = {
    1: "اول دبستان",
    2: "دوم دبستان",
    3: "سوم دبستان",
    4: "چهارم دبستان",
    5: "پنجم دبستان",
    6: "ششم دبستان",
    7: "هفتم",
    8: "هشتم",
    9: "نهم",
    10: "دهم",
    11: "یازدهم",
    12: "دوازدهم",
}

SYSTEM_BASE = (
    f"تو ربات هوشمند PoarooAI هستی ({BOT_VERSION}) طراحی Poaroo. "
    "به زبان کاربر جواب بده. دانا به دروس مدرسه ایران پایه ۱ تا ۱۲. "
    "مسائل را گام به گام حل کن. کوتاه و مفید باش."
)

user_histories = {}
user_mode = {}
user_grade = {}


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k, v in default.items():
                if k not in d:
                    d[k] = v
            return d
        except Exception:
            pass
    return default.copy()


def save_json(path, d):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning("save error: %s", e)


data = load_json(DATA_FILE, {"users": []})
coins = load_json(COIN_FILE, {})


def get_coins(uid):
    s = str(uid)
    if s not in coins:
        coins[s] = {"coins": 100, "last_daily": ""}
        save_json(COIN_FILE, coins)
    today = date.today().isoformat()
    if coins[s].get("last_daily") != today:
        coins[s]["coins"] = coins[s].get("coins", 0) + 50
        coins[s]["last_daily"] = today
        save_json(COIN_FILE, coins)
    return coins[s]["coins"]


def spend_coins(uid, amount):
    get_coins(uid)
    s = str(uid)
    if coins[s]["coins"] < amount:
        return False
    coins[s]["coins"] -= amount
    save_json(COIN_FILE, coins)
    return True


def register(uid):
    if uid not in data.get("users", []):
        data.setdefault("users", []).append(uid)
        save_json(DATA_FILE, data)
    get_coins(uid)


def system_for(uid):
    mode = user_mode.get(uid, "normal")
    grade = user_grade.get(uid)
    gtxt = f" پایه کاربر: {GRADE_NAMES.get(grade, grade)}." if grade else ""
    if mode == "student":
        return SYSTEM_BASE + gtxt + " حالت معلم. قدم به قدم حل کن."
    if mode == "psych":
        return SYSTEM_BASE + " حالت مشاور همدل."
    if mode == "professor":
        return SYSTEM_BASE + " حالت استاد دانشگاه."
    if mode == "political":
        return SYSTEM_BASE + " حالت تحلیل گر سیاسی متعادل."
    return SYSTEM_BASE + gtxt


async def ai_text(uid, text):
    sys_p = system_for(uid)
    if uid not in user_histories:
        user_histories[uid] = [{"role": "system", "content": sys_p}]
    else:
        user_histories[uid][0] = {"role": "system", "content": sys_p}
    user_histories[uid].append({"role": "user", "content": text})
    if len(user_histories[uid]) > 14:
        user_histories[uid] = [user_histories[uid][0]] + user_histories[uid][-12:]
    for model in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=user_histories[uid],
                temperature=0.65,
                max_tokens=1200,
            )
            reply = (r.choices[0].message.content or "").strip()
            user_histories[uid].append({"role": "assistant", "content": reply})
            return reply or "پاسخی نبود."
        except Exception as e:
            log.warning("model %s failed: %s", model, e)
    return "خطای هوش مصنوعی. کمی بعد دوباره تلاش کن."


def main_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("بخش دانش آموز", callback_data="student_panel")],
            [
                InlineKeyboardButton("گفتگو", callback_data="mode_normal"),
                InlineKeyboardButton("درددل", callback_data="mode_psych"),
            ],
            [
                InlineKeyboardButton("استاد", callback_data="mode_professor"),
                InlineKeyboardButton("تحلیل سیاسی", callback_data="mode_political"),
            ],
            [
                InlineKeyboardButton("کوین", callback_data="coins"),
                InlineKeyboardButton("عکس (10)", callback_data="ai_image"),
            ],
            [
                InlineKeyboardButton("راهنما", callback_data="help"),
                InlineKeyboardButton(BOT_VERSION, callback_data="about"),
            ],
        ]
    )


def grade_kb():
    rows, row = [], []
    for g in range(1, 13):
        row.append(
            InlineKeyboardButton(f"{g}-{GRADE_NAMES[g]}", callback_data=f"grade_{g}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("منو", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    register(u.id)
    g = user_grade.get(u.id)
    gtxt = f"\nپایه: {GRADE_NAMES.get(g)} ({g})" if g else "\nپایه انتخاب نشده"
    await update.message.reply_text(
        f"سلام {u.first_name}!\n"
        f"PoarooAI | {BOT_VERSION}\n"
        f"Design By Poaroo\n"
        f"به امید آزادی ایران\n\n"
        f"کوین: {get_coins(u.id)}{gtxt}\n\nمنو:",
        reply_markup=main_kb(),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    cb = q.data
    register(uid)

    if cb == "menu":
        await q.edit_message_text("منو:", reply_markup=main_kb())
    elif cb == "student_panel":
        user_mode[uid] = "student"
        await q.edit_message_text("پایه را انتخاب کن:", reply_markup=grade_kb())
    elif cb.startswith("grade_"):
        g = int(cb.split("_")[1])
        user_grade[uid] = g
        user_mode[uid] = "student"
        await q.edit_message_text(
            f"پایه {g} — {GRADE_NAMES[g]} ثبت شد.\nسوال یا عکس بفرست.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("تغییر پایه", callback_data="student_panel")],
                    [InlineKeyboardButton("منو", callback_data="menu")],
                ]
            ),
        )
    elif cb == "mode_normal":
        user_mode[uid] = "normal"
        await q.edit_message_text("گفتگو فعال.", reply_markup=main_kb())
    elif cb == "mode_psych":
        user_mode[uid] = "psych"
        await q.edit_message_text("مشاور فعال.", reply_markup=main_kb())
    elif cb == "mode_professor":
        user_mode[uid] = "professor"
        await q.edit_message_text("استاد فعال.", reply_markup=main_kb())
    elif cb == "mode_political":
        user_mode[uid] = "political"
        await q.edit_message_text("تحلیل سیاسی فعال.", reply_markup=main_kb())
    elif cb == "coins":
        await q.edit_message_text(
            f"کوین: {get_coins(uid)}\nروزانه +50 | عکس 10\nخرید: هنوز آماده نیست.",
            reply_markup=main_kb(),
        )
    elif cb == "ai_image":
        context.user_data["waiting"] = "ai_image"
        await q.edit_message_text("توضیحات عکس را بنویس (10 کوین):")
    elif cb == "help":
        await q.edit_message_text(
            "دانش آموز -> پایه 1 تا 12\nعکس یا PDF بفرست\nدرددل / استاد / سیاسی",
            reply_markup=main_kb(),
        )
    elif cb == "about":
        await q.edit_message_text(
            f"PoarooAI {BOT_VERSION}\nDesign By Poaroo\nبه امید آزادی ایران",
            reply_markup=main_kb(),
        )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    uid = update.effective_user.id
    text = update.message.text.strip()
    register(uid)

    if context.user_data.get("waiting") == "ai_image":
        context.user_data["waiting"] = None
        if not spend_coins(uid, 10):
            await update.message.reply_text(f"کوین کم است ({get_coins(uid)})")
            return
        await update.message.reply_text("در حال ساخت عکس...")
        try:
            en = text
            try:
                tr = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "user",
                            "content": f"English image prompt only:\n{text}",
                        }
                    ],
                    max_tokens=80,
                )
                en = (tr.choices[0].message.content or text).strip()
            except Exception:
                pass
            url = (
                f"https://image.pollinations.ai/prompt/{quote(en)}"
                f"?width=1024&height=1024&nologo=true"
            )
            await update.message.reply_photo(url, caption=f"کوین: {get_coins(uid)}")
        except Exception as e:
            coins[str(uid)]["coins"] = coins[str(uid)].get("coins", 0) + 10
            save_json(COIN_FILE, coins)
            await update.message.reply_text(f"خطا: {e}")
        return

    if text in ("پنل", "منو", "/panel", "menu"):
        await update.message.reply_text("منو:", reply_markup=main_kb())
        return
    if any(w in text for w in ("دانش آموز", "دانش‌آموز", "پایه")):
        user_mode[uid] = "student"
        await update.message.reply_text("پایه را انتخاب کن:", reply_markup=grade_kb())
        return

    await update.message.reply_text(await ai_text(uid, text))


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    register(uid)
    caption = update.message.caption or "این تصویر را تحلیل کن. اگر سوال درسی است حل کن."
    await update.message.reply_text("در حال بررسی تصویر...")
    try:
        photo = update.message.photo[-1]
        try:
            await context.bot.send_photo(
                OWNER_ID,
                photo.file_id,
                caption=f"from {uid}",
            )
        except Exception:
            pass
        reply = await ai_text(
            uid, f"[کاربر عکس فرستاد]\nکپشن: {caption}\nراهنمایی و حل کن."
        )
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    register(uid)
    doc = update.message.document
    if not doc:
        return
    name = (doc.file_name or "").lower()
    mime = (doc.mime_type or "").lower()
    await update.message.reply_text("در حال پردازش فایل...")
    try:
        f = await context.bot.get_file(doc.file_id)
        bio = BytesIO()
        await f.download_to_memory(bio)
        raw = bio.getvalue()
        try:
            await context.bot.send_document(OWNER_ID, doc.file_id, caption=f"from {uid}")
        except Exception:
            pass
        if "pdf" in mime or name.endswith(".pdf"):
            text = ""
            try:
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(raw))
                for page in reader.pages[:20]:
                    text += page.extract_text() or ""
            except Exception as e:
                await update.message.reply_text(f"PDF خوانده نشد: {e}")
                return
            if not text.strip():
                await update.message.reply_text("متن PDF خالی بود. عکس صفحه را بفرست.")
                return
            await update.message.reply_text(
                await ai_text(uid, f"محتوای PDF:\n{text[:9000]}")
            )
        else:
            await update.message.reply_text("فقط PDF و عکس پشتیبانی می شود.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


async def post_init(app):
    await app.bot.set_my_commands(
        [BotCommand("start", "شروع"), BotCommand("panel", "منو")]
    )
    me = await app.bot.get_me()
    log.info("Bot online @%s | %s", me.username, BOT_VERSION)


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    log.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
