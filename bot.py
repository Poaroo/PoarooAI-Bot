# -*- coding: utf-8 -*-
"""SibillSecure - Aisecure3 By Poaroo | با ساخت عکس اصلاح‌شده"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, InputFile, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus, ChatType
from openai import OpenAI
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict, deque
from urllib.parse import quote
import pytz, requests, random, json, os, asyncio, re

TELEGRAM_TOKEN = "8736271151:AAFJhuhNwC7hY-zCdDS_ID4_b9gV3c_PoVg"
GROQ_API_KEY = "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"
OWNER_ID = 6130352235
SUPPORT_ID = 8692469832
SUPPORT_USERNAME = "@CyberGuarSupport"
SUB_LINK = "https://svn.mobiletanaz.com:2053/sub/djMsMTg3MjUzLDE3ODgxNDUwODQ.ytONU85fiU9-62cyN-3OAK1wPStAlPXezRqXwgpF8NU"
BOT_VERSION = "Aisecure3 By Poaroo"

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
DATA_FILE = "bot_data.json"
DEFAULT = {"admins":[],"group_admins":{},"users":[],"warnings":{},"last_active":{},"mute_list":{},
           "msg_count":{},"invite_count":{},"total_messages":{},"left_members":{},"member_count":{},
           "filters":[],"started_users":[],"groups":[],"group_settings":{},"group_owners":{},"bot_online":True}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            d = json.load(open(DATA_FILE, encoding="utf-8"))
            for k,v in DEFAULT.items():
                if k not in d: d[k]=v
            return d
        except: pass
    return DEFAULT.copy()

def save_data(d):
    try: json.dump(d, open(DATA_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception as e: print(e)

data = load_data()
user_histories = {}
spam_tracker = defaultdict(lambda: deque(maxlen=15))
last_panel = {}
dice_games = {}

SYSTEM_PROMPT = "You are SibillSecure (Aisecure3 By Poaroo), a friendly smart Telegram bot. Reply in the user's language. Be warm and concise."

def is_owner(uid): return uid==OWNER_ID
def is_filter_manager(uid): return uid in (OWNER_ID, SUPPORT_ID)
def is_global_admin(uid): return is_owner(uid) or uid in data.get("admins",[])
def is_group_admin(uid, gid):
    if is_global_admin(uid): return True
    g=str(gid)
    if str(uid)==data.get("group_owners",{}).get(g): return True
    return str(uid) in data.get("group_admins",{}).get(g,[])

def get_gs(gid):
    g=str(gid)
    data.setdefault("group_settings",{})
    if g not in data["group_settings"]:
        data["group_settings"][g]={"welcome":True,"only_admin":False,"quiet":False,"silent":False,"locked":False,"anti_link":False,"free_chat":True}
        save_data(data)
    gs=data["group_settings"][g]
    gs.setdefault("free_chat", True)
    return gs

def register_user(uid):
    data.setdefault("users",[])
    if uid not in data["users"]: data["users"].append(uid); save_data(data)

def register_group(gid):
    data.setdefault("groups",[])
    g=str(gid)
    if g not in data["groups"]: data["groups"].append(g); save_data(data)

def get_time_tehran():
    now=datetime.now(pytz.timezone("Asia/Tehran"))
    days={"Saturday":"شنبه","Sunday":"یکشنبه","Monday":"دوشنبه","Tuesday":"سه‌شنبه","Wednesday":"چهارشنبه","Thursday":"پنج‌شنبه","Friday":"جمعه"}
    return f"📅 {now.strftime('%Y/%m/%d')} | {days.get(now.strftime('%A'),'')}\n🕐 {now.strftime('%H:%M')}"

def get_weather(city):
    try:
        geo=requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=fa&format=json",timeout=10).json()
        if not geo.get("results"): return f"❌ شهر «{city}» پیدا نشد."
        loc=geo["results"][0]; lat,lon=loc["latitude"],loc["longitude"]
        w=requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=auto",timeout=10).json()["current"]
        codes={0:"آفتابی ☀️",1:"صاف 🌤",2:"نیمه‌ابری ⛅",3:"ابری ☁️",45:"مه 🌫",61:"باران 🌧",71:"برف ❄️",95:"رعد ⛈"}
        return f"🌤 **{loc.get('name',city)}**\n🌡 {w['temperature_2m']}°C\n💧 {w['relative_humidity_2m']}%\n💨 {w['wind_speed_10m']} km/h\n{codes.get(w['weather_code'],'')}"
    except: return "آب‌وهوا در دسترس نیست."

async def ai_reply(uid, text, quiet=False):
    if uid not in user_histories: user_histories[uid]=[{"role":"system","content":SYSTEM_PROMPT}]
    user_histories[uid].append({"role":"user","content":text})
    if len(user_histories[uid])>14: user_histories[uid]=[user_histories[uid][0]]+user_histories[uid][-12:]
    try:
        r=client.chat.completions.create(model="openai/gpt-oss-20b",messages=user_histories[uid],
            temperature=0.5 if quiet else 0.9, max_tokens=90 if quiet else 400)
        reply=r.choices[0].message.content.strip()
        user_histories[uid].append({"role":"assistant","content":reply}); return reply
    except Exception as e: print(e); return "متأسفم، مشکل پیش اومد 🙏"

async def generate_joke():
    try:
        r=client.chat.completions.create(model="openai/gpt-oss-20b",
            messages=[{"role":"system","content":"جوک کوتاه فارسی بامزه. فقط جوک."},{"role":"user","content":"جوک"}],temperature=1.2,max_tokens=120)
        return r.choices[0].message.content.strip()
    except: return "چرا سرور سردشه؟ چون فن داره 😂"

async def translate_to_en(prompt):
    """ترجمه توضیحات به انگلیسی برای کیفیت عکس"""
    try:
        r=client.chat.completions.create(model="openai/gpt-oss-20b",
            messages=[{"role":"system","content":"Translate to a detailed vivid English AI image prompt. Output ONLY English, no quotes."},
                      {"role":"user","content":prompt}], temperature=0.2, max_tokens=180)
        return r.choices[0].message.content.strip()
    except: return prompt

def ai_image_url(en_prompt):
    return f"https://image.pollinations.ai/prompt/{quote(en_prompt)}?width=1024&height=1024&nologo=true&enhance=true&model=flux"

def create_sticker_image(text):
    size=512; img=Image.new("RGBA",(size,size),(0,0,0,0)); draw=ImageDraw.Draw(img)
    for i in range(size//2,0,-2):
        draw.ellipse([size//2-i,size//2-i,size//2+i,size//2+i], fill=(25+i//5,30+i//6,70+i//3,200))
    try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",68)
    except: font=ImageFont.load_default()
    words=text[:16]; bbox=draw.textbbox((0,0),words,font=font)
    w,h=bbox[2]-bbox[0],bbox[3]-bbox[1]; x,y=(size-w)/2,(size-h)/2-12
    draw.text((x+2,y+2),words,font=font,fill=(0,0,0,150)); draw.text((x,y),words,font=font,fill=(255,255,255,255))
    bio=BytesIO(); bio.name="sticker.webp"; img.save(bio,"WEBP",quality=95); bio.seek(0); return bio

async def delete_old_panel(context, chat_id):
    mid=last_panel.get(chat_id)
    if mid:
        try: await context.bot.delete_message(chat_id, mid)
        except: pass
        last_panel.pop(chat_id, None)

async def send_panel(update, context, text, kb):
    await delete_old_panel(context, update.effective_chat.id)
    msg=await update.effective_message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    last_panel[update.effective_chat.id]=msg.message_id; return msg

def has_link(t):
    return bool(t and re.search(r'https?://|www\.|t\.me/', t, re.I))

def main_panel_for(uid, chat_type, chat_id=None):
    is_group=chat_type in ("group","supergroup")
    is_gadmin=is_group and chat_id and is_group_admin(uid, chat_id)
    kb=[
        [InlineKeyboardButton("🟢 زمان",callback_data="time"),InlineKeyboardButton("🔵 آب‌وهوا",callback_data="weather")],
        [InlineKeyboardButton("🟡 تاس",callback_data="dice"),InlineKeyboardButton("🟣 جوک",callback_data="joke")],
        [InlineKeyboardButton("🟠 محاسبه",callback_data="math"),InlineKeyboardButton("🟤 استیکر",callback_data="sticker")],
        [InlineKeyboardButton("🎨 ساخت عکس AI",callback_data="ai_image")],
        [InlineKeyboardButton("🛡 خرید فیلتر",callback_data="buy_filter")],
        [InlineKeyboardButton("➕ افزودن به گروه",callback_data="add_to_group_btn")],
        [InlineKeyboardButton("🐛 گزارش مشکل",callback_data="report_bug")],
    ]
    if is_group:
        kb.append([InlineKeyboardButton("🔇 لیست سکوت",callback_data="mute_list")])
        kb.append([InlineKeyboardButton("📊 آمار",callback_data="do_stats")])
        if is_gadmin or is_owner(uid) or is_global_admin(uid):
            kb += [[InlineKeyboardButton("📢 تگ",callback_data="tag_menu")],
                   [InlineKeyboardButton("🎛 تنظیمات گروه",callback_data="group_settings")],
                   [InlineKeyboardButton("📋 گزارش پیوی",callback_data="full_report")]]
    if is_owner(uid) or uid==SUPPORT_ID:
        kb.append([InlineKeyboardButton("⚙️ مدیریت فیلتر",callback_data="manage_filters")])
    if is_owner(uid):
        kb += [[InlineKeyboardButton("📢 همگانی",callback_data="owner_broadcast")],
               [InlineKeyboardButton("📊 آمار کل",callback_data="owner_stats")],
               [InlineKeyboardButton("👥 مدیران",callback_data="owner_admins"),InlineKeyboardButton("➕ مدیر",callback_data="owner_addadmin")]]
    kb.append([InlineKeyboardButton("⬛ بستن",callback_data="close_panel")])
    return InlineKeyboardMarkup(kb)

def group_settings_panel(gid):
    gs=get_gs(gid)
    def s(k): return "✅" if gs.get(k) else "❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"خوش‌آمد {s('welcome')}",callback_data="tg_welcome")],
        [InlineKeyboardButton(f"مکالمه آزاد {s('free_chat')}",callback_data="tg_freechat")],
        [InlineKeyboardButton(f"فقط مدیر {s('only_admin')}",callback_data="tg_only_admin")],
        [InlineKeyboardButton(f"کم‌حرف {s('quiet')}",callback_data="tg_quiet")],
        [InlineKeyboardButton(f"ساکت {s('silent')}",callback_data="tg_silent")],
        [InlineKeyboardButton(f"ضد لینک {s('anti_link')}",callback_data="tg_antilink")],
        [InlineKeyboardButton("🔒 قفل" if not gs.get("locked") else "🔓 باز",callback_data="tg_lock")],
        [InlineKeyboardButton("⬛ بستن",callback_data="close_panel")],
    ])

def tag_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 مدیران",callback_data="tag_admins")],
        [InlineKeyboardButton("👥 ۱۰۰",callback_data="tag_100")],
        [InlineKeyboardButton("👥 ۳۰۰",callback_data="tag_300")],
        [InlineKeyboardButton("⬛",callback_data="close_panel")],
    ])

def filters_kb():
    kb=[[InlineKeyboardButton(f"{f['country']}|{f['price']}|{f['volume']}|{f['duration']}",callback_data=f"buy_{i}")]
        for i,f in enumerate(data.get("filters",[]))]
    if not kb: kb=[[InlineKeyboardButton("خالی",callback_data="none")]]
    kb.append([InlineKeyboardButton("⬛",callback_data="close_panel")])
    return InlineKeyboardMarkup(kb)

def manage_filters_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕",callback_data="add_filter"),InlineKeyboardButton("🗑",callback_data="del_filter")],
        [InlineKeyboardButton("📋",callback_data="list_filters"),InlineKeyboardButton("🔗 ساب",callback_data="show_sub")],
        [InlineKeyboardButton("⬛",callback_data="close_panel")],
    ])

async def start(update, context):
    user=update.effective_user; uid=user.id; register_user(uid)
    data.setdefault("last_active",{})[str(uid)]=datetime.now().isoformat()
    if not data.get("bot_online",True) and not is_owner(uid):
        await update.message.reply_text("🔴 خاموش است."); return
    data.setdefault("started_users",[])
    if uid not in data["started_users"]:
        data["started_users"].append(uid); save_data(data)
        await update.message.reply_text(f"سلام {user.first_name}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Start",callback_data="startbot")]]))
        return
    save_data(data)
    bot=await context.bot.get_me()
    await update.message.reply_text(f"سلام {user.first_name}!\nمن @{bot.username}\n**{BOT_VERSION}**\nبگو **پنل**", parse_mode="Markdown")

async def open_panel(update, context):
    uid=update.effective_user.id; chat=update.effective_chat; register_user(uid)
    title="👑 مالک" if is_owner(uid) else ("🛡 مدیر" if is_global_admin(uid) or uid==SUPPORT_ID or (chat.type in ("group","supergroup") and is_group_admin(uid,chat.id)) else "📱 کاربر")
    await send_panel(update, context, f"**پنل {title}** ✨", main_panel_for(uid, chat.type, chat.id))

async def build_stats(gid):
    g=str(gid)
    total=data.get("total_messages",{}).get(g,0)
    members=data.get("member_count",{}).get(g,"؟")
    left=data.get("left_members",{}).get(g,0)
    counts=data.get("msg_count",{}).get(g,{})
    top10=sorted(counts.items(),key=lambda x:x[1],reverse=True)[:10]
    top10_txt="\n".join(f"{i+1}. `{u}` → {c}" for i,(u,c) in enumerate(top10)) or "—"
    muted=len(data.get("mute_list",{}).get(g,{}))
    return f"📊 پیام:{total} عضو:{members} خروج:{left} سکوت:{muted}\n🏆\n{top10_txt}"

async def mute_user(bot, chat_id, user_id, minutes=0, by_id=None):
    try:
        await bot.restrict_chat_member(chat_id, user_id, permissions=ChatPermissions(can_send_messages=False))
        gid,uid=str(chat_id),str(user_id)
        data.setdefault("mute_list",{}).setdefault(gid,{})[uid]={"until":(datetime.now()+timedelta(minutes=minutes)).isoformat() if minutes else "نامحدود","by":by_id}
        save_data(data)
        if minutes>0:
            async def later():
                await asyncio.sleep(minutes*60)
                try:
                    await bot.restrict_chat_member(chat_id,user_id,permissions=ChatPermissions(can_send_messages=True,can_send_media_messages=True,can_send_other_messages=True,can_add_web_page_previews=True))
                    data.get("mute_list",{}).get(gid,{}).pop(uid,None); save_data(data)
                except: pass
            asyncio.create_task(later())
        return True
    except: return False

async def unmute_user(bot, chat_id, user_id):
    try:
        await bot.restrict_chat_member(chat_id,user_id,permissions=ChatPermissions(can_send_messages=True,can_send_media_messages=True,can_send_other_messages=True,can_add_web_page_previews=True))
        data.get("mute_list",{}).get(str(chat_id),{}).pop(str(user_id),None); save_data(data); return True
    except: return False

async def lock_group(bot, chat_id):
    try:
        await bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
        get_gs(chat_id)["locked"]=True; save_data(data); return True
    except: return False

async def unlock_group(bot, chat_id):
    try:
        await bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True,can_send_media_messages=True,can_send_other_messages=True,can_add_web_page_previews=True,can_send_polls=True))
        get_gs(chat_id)["locked"]=False; save_data(data); return True
    except: return False

async def play_dice(query, context):
    uid=query.from_user.id
    if uid not in dice_games: dice_games[uid]={"user":0,"bot":0}
    try:
        u_dice=await query.message.reply_dice(emoji="🎲"); await asyncio.sleep(3)
        b_dice=await context.bot.send_dice(query.message.chat_id, emoji="🎲"); await asyncio.sleep(3)
        ur,br=u_dice.dice.value, b_dice.dice.value
    except:
        ur,br=random.randint(1,6),random.randint(1,6)
    if ur>br: dice_games[uid]["user"]+=1; res="🎉 تو!"
    elif br>ur: dice_games[uid]["bot"]+=1; res="😈 من!"
    else: res="🤝"
    u,b=dice_games[uid]["user"],dice_games[uid]["bot"]
    text=f"تو:{ur} من:{br}\n{res}\nامتیاز → تو:**{u}** ربات:**{b}**"
    if u>=5 or b>=5:
        text+="\n🏆 "+("قهرمان تو!" if u>=5 else "من بردم!")
        dice_games[uid]={"user":0,"bot":0}
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 جدید",callback_data="dice")]])
    else:
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 دوباره",callback_data="dice_roll")]])
    try: await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    except: await context.bot.send_message(query.message.chat_id, text, reply_markup=kb, parse_mode="Markdown")

async def button_handler(update, context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id; cb=q.data; chat=q.message.chat; gid=chat.id
    if cb=="close_panel":
        try: await q.message.delete()
        except:
            try: await q.edit_message_text("بسته شد")
            except: pass
        last_panel.pop(gid,None); return
    if cb=="none": await q.answer("خالی",show_alert=True); return
    if cb=="startbot":
        bot=await context.bot.get_me()
        await q.edit_message_text(f"من @{bot.username}\n**{BOT_VERSION}**\nبه گروه اضافه شم؟",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ بله",callback_data="add_to_group")],[InlineKeyboardButton("❌",callback_data="no_group")]]), parse_mode="Markdown"); return
    if cb in ("add_to_group","add_to_group_btn"):
        bot=await context.bot.get_me()
        await q.edit_message_text(f"https://t.me/{bot.username}?startgroup=true\nبعد ادمینم کن."); return
    if cb=="no_group": await q.edit_message_text("باشه 😊"); return
    if cb=="report_bug":
        context.user_data["waiting"]="report_bug"; await q.edit_message_text("🐛 مشکل را بنویس:"); return
    if cb=="ai_image":
        context.user_data["waiting"]="ai_image"
        await q.edit_message_text("🎨 توضیحات عکس را بنویس:\nمثال: یک گربه فضانورد روی مریخ"); return
    if cb=="group_settings":
        if not is_group_admin(uid,gid): await q.answer("فقط مدیر",show_alert=True); return
        await q.edit_message_text("🎛 تنظیمات", reply_markup=group_settings_panel(gid)); return
    if cb=="full_report":
        if not is_group_admin(uid,gid): await q.answer("فقط مدیر",show_alert=True); return
        try:
            await context.bot.send_message(uid, f"📋 {chat.title}\n{await build_stats(gid)}", parse_mode="Markdown")
            await q.edit_message_text("✅ به پیوی رفت.")
        except: await q.edit_message_text("اول /start در پیوی")
        return
    if cb in ("tg_welcome","tg_only_admin","tg_quiet","tg_silent","tg_lock","tg_antilink","tg_freechat"):
        if not is_group_admin(uid,gid): await q.answer("فقط مدیر",show_alert=True); return
        gs=get_gs(gid)
        if cb=="tg_lock":
            ok=await (unlock_group if gs.get("locked") else lock_group)(context.bot,gid)
            await q.answer("انجام شد" if ok else "خطا")
        else:
            key={"tg_welcome":"welcome","tg_only_admin":"only_admin","tg_quiet":"quiet","tg_silent":"silent","tg_antilink":"anti_link","tg_freechat":"free_chat"}[cb]
            gs[key]=not gs.get(key,False); save_data(data)
        await q.edit_message_text("🎛 تنظیمات", reply_markup=group_settings_panel(gid)); return
    if cb=="time": await q.edit_message_text(get_time_tehran())
    elif cb=="joke": await q.edit_message_text(f"😂 {await generate_joke()}")
    elif cb=="weather": context.user_data["waiting"]="weather"; await q.edit_message_text("شهر:")
    elif cb=="math": context.user_data["waiting"]="math"; await q.edit_message_text("محاسبه:")
    elif cb=="sticker": context.user_data["waiting"]="sticker"; await q.edit_message_text("متن استیکر:")
    elif cb=="dice":
        dice_games[uid]={"user":0,"bot":0}
        await q.edit_message_text("🎲 تا ۵ امتیاز\nتو:0 ربات:0", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 تاس!",callback_data="dice_roll")]]))
    elif cb=="dice_roll": await play_dice(q, context)
    elif cb=="mute_list":
        lines=["🔇 سکوت\n"]
        for u,info in data.get("mute_list",{}).get(str(gid),{}).items():
            lines.append(f"• `{u}` | {str(info.get('until','?'))[:19]}")
        if len(lines)==1: lines.append("خالی")
        await q.edit_message_text("\n".join(lines), parse_mode="Markdown")
    elif cb=="do_stats": await q.edit_message_text(await build_stats(gid), parse_mode="Markdown")
    elif cb=="tag_menu":
        if not is_group_admin(uid,gid): await q.answer("فقط مدیر",show_alert=True); return
        await q.edit_message_text("📢", reply_markup=tag_menu())
    elif cb=="tag_admins":
        try:
            admins=await context.bot.get_chat_administrators(gid)
            m=" ".join(f"<a href='tg://user?id={a.user.id}'>{a.user.first_name}</a>" for a in admins if not a.user.is_bot)
            await context.bot.send_message(gid, "👑 "+m, parse_mode="HTML"); await q.edit_message_text("✅")
        except Exception as e: await q.edit_message_text(str(e))
    elif cb in ("tag_100","tag_300"):
        n=100 if cb=="tag_100" else 300
        users=list(data.get("msg_count",{}).get(str(gid),{}).keys())
        if not users: await q.edit_message_text("کاربری نیست"); return
        sel=random.sample(users, min(n,len(users)))
        for i in range(0,len(sel),40):
            try: await context.bot.send_message(gid, "📢 "+" ".join(f"<a href='tg://user?id={u}'>‌</a>" for u in sel[i:i+40]), parse_mode="HTML")
            except: pass
            await asyncio.sleep(0.3)
        await q.edit_message_text(f"✅ {len(sel)}")
    elif cb=="buy_filter": await q.edit_message_text("🛡", reply_markup=filters_kb())
    elif cb.startswith("buy_"):
        try: f=data["filters"][int(cb.split("_")[1])]
        except: await q.answer("نیست",show_alert=True); return
        await q.edit_message_text(f"✅ {f['country']} | {f['price']}\n{SUPPORT_USERNAME}")
        try:
            cap=f"🛒 {q.from_user.full_name} `{q.from_user.id}`\n{f['country']}|{f['price']}|{f['volume']}|{f['duration']}"
            if f.get("file_id"): await context.bot.send_document(SUPPORT_ID,f["file_id"],caption=cap,parse_mode="Markdown")
            else: await context.bot.send_message(SUPPORT_ID,cap,parse_mode="Markdown")
        except: pass
    elif cb=="manage_filters":
        if not is_filter_manager(uid): await q.answer("نداری",show_alert=True); return
        await q.edit_message_text("⚙️", reply_markup=manage_filters_kb())
    elif cb=="show_sub":
        if is_filter_manager(uid): await q.edit_message_text(f"`{SUB_LINK}`", parse_mode="Markdown")
    elif cb=="add_filter":
        if is_filter_manager(uid):
            context.user_data["waiting"]="add_filter_info"; await q.edit_message_text("`کشور | قیمت | حجم | مدت`", parse_mode="Markdown")
    elif cb=="list_filters":
        if is_filter_manager(uid):
            fs=data.get("filters",[])
            await q.edit_message_text("\n".join(f"{i+1}. {f['country']}|{f['price']}" for i,f in enumerate(fs)) or "خالی")
    elif cb=="del_filter":
        if is_filter_manager(uid):
            fs=data.get("filters",[])
            if not fs: await q.edit_message_text("خالی"); return
            kb=[[InlineKeyboardButton(f"🗑 {f['country']}",callback_data=f"delf_{i}")] for i,f in enumerate(fs)]
            kb.append([InlineKeyboardButton("⬛",callback_data="manage_filters")])
            await q.edit_message_text("حذف؟", reply_markup=InlineKeyboardMarkup(kb))
    elif cb.startswith("delf_") and is_filter_manager(uid):
        try:
            r=data["filters"].pop(int(cb.split("_")[1])); save_data(data); await q.edit_message_text(f"✅ {r['country']}")
        except: pass
    elif cb=="owner_stats" and is_owner(uid):
        await q.edit_message_text(f"کاربر:{len(data.get('users',[]))} گروه:{len(data.get('groups',[]))} پیام:{sum(data.get('total_messages',{}).values())}")
    elif cb=="owner_admins" and is_owner(uid):
        await q.edit_message_text("مدیران:\n"+("\n".join(f"`{a}`" for a in data.get("admins",[])) or "هیچ"), parse_mode="Markdown")
    elif cb=="owner_addadmin" and is_owner(uid):
        context.user_data["waiting"]="addadmin"; await q.edit_message_text("آیدی:")
    elif cb=="owner_broadcast" and is_owner(uid):
        context.user_data["waiting"]="broadcast"; await q.edit_message_text("پیام:")

async def handle_message(update, context):
    if not update.message: return
    user=update.effective_user; uid=user.id; chat=update.effective_chat
    text=(update.message.text or "").strip()
    register_user(uid)
    data.setdefault("last_active",{})[str(uid)]=datetime.now().isoformat()

    if not data.get("bot_online",True) and not is_owner(uid):
        if chat.type==ChatType.PRIVATE: await update.message.reply_text("🔴 خاموش")
        return

    if is_owner(uid) and chat.type==ChatType.PRIVATE:
        if text in ("خاموش","offline"):
            data["bot_online"]=False; save_data(data)
            for x in list(data.get("users",[]))+[int(g) for g in data.get("groups",[])]:
                try: await context.bot.send_message(x,"🔴 خاموش شد")
                except: pass
            await update.message.reply_text("✅"); return
        if text in ("روشن","online"):
            data["bot_online"]=True; save_data(data)
            bot=await context.bot.get_me(); msg=f"🟢 @{bot.username}\n{BOT_VERSION}"
            for x in list(data.get("users",[]))+[int(g) for g in data.get("groups",[])]:
                try: await context.bot.send_message(x,msg)
                except: pass
            await update.message.reply_text("✅"); return
        if text in ("آمار","stats"):
            await update.message.reply_text(f"کاربر:{len(data.get('users',[]))} گروه:{len(data.get('groups',[]))}"); return

    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        register_group(chat.id); gid=str(chat.id)
        data.setdefault("msg_count",{}).setdefault(gid,{})
        data.setdefault("total_messages",{})
        data["msg_count"][gid][str(uid)]=data["msg_count"][gid].get(str(uid),0)+1
        data["total_messages"][gid]=data["total_messages"].get(gid,0)+1; save_data(data)
        gs=get_gs(chat.id)
        if gs.get("anti_link") and has_link(text) and not is_group_admin(uid,chat.id):
            try: await update.message.delete()
            except: pass
            data.setdefault("warnings",{}).setdefault(gid,{})
            data["warnings"][gid][str(uid)]=data["warnings"][gid].get(str(uid),0)+1
            cnt=data["warnings"][gid][str(uid)]; save_data(data)
            await context.bot.send_message(chat.id, f"⚠️ لینک {cnt}/3")
            if cnt>=3:
                try: await context.bot.ban_chat_member(chat.id,uid); data["warnings"][gid][str(uid)]=0; save_data(data)
                except: pass
            return
        key=f"{gid}:{uid}"; spam_tracker[key].append(text)
        if len(spam_tracker[key])>=10 and len(set(spam_tracker[key]))==1 and text:
            await mute_user(context.bot,chat.id,uid,minutes=1)
            await update.message.reply_text("🚫 اسپم — سکوت ۱د"); spam_tracker[key].clear(); return

    if update.message.photo or update.message.video or update.message.document:
        if context.user_data.get("waiting")=="add_filter_file" and is_filter_manager(uid):
            fid=(update.message.document.file_id if update.message.document else update.message.photo[-1].file_id if update.message.photo else None)
            if fid and context.user_data.get("new_filter"):
                nf=context.user_data["new_filter"]; nf["file_id"]=fid
                data.setdefault("filters",[]).append(nf); save_data(data)
                context.user_data["waiting"]=None; context.user_data["new_filter"]=None
                await update.message.reply_text(f"✅ {nf['country']}"); return
        try:
            s=f"{user.full_name} `{uid}` | {chat.title or 'خصوصی'}"
            if update.message.photo: await context.bot.send_photo(OWNER_ID,update.message.photo[-1].file_id,caption=f"📷 {s}",parse_mode="Markdown")
            elif update.message.video: await context.bot.send_video(OWNER_ID,update.message.video.file_id,caption=f"🎬 {s}",parse_mode="Markdown")
            elif update.message.document: await context.bot.send_document(OWNER_ID,update.message.document.file_id,caption=f"📎 {s}",parse_mode="Markdown")
        except: pass
        return

    if not text: return
    low=text.lower().strip()

    if low in ("پنل","panel","منو") or text=="/panel": await open_panel(update,context); return
    if low in ("پنل گفتگو","تنظیمات گروه") and chat.type in (ChatType.GROUP,ChatType.SUPERGROUP):
        if not is_group_admin(uid,chat.id): await update.message.reply_text("فقط مدیر"); return
        await send_panel(update,context,"🎛",group_settings_panel(chat.id)); return
    if low in ("تگ","tag") and chat.type in (ChatType.GROUP,ChatType.SUPERGROUP):
        if not is_group_admin(uid,chat.id): await update.message.reply_text("فقط مدیر"); return
        await send_panel(update,context,"📢",tag_menu()); return
    if low in ("آمار","stats") and chat.type in (ChatType.GROUP,ChatType.SUPERGROUP):
        await update.message.reply_text(await build_stats(chat.id), parse_mode="Markdown"); return
    if low=="گزارش" and chat.type in (ChatType.GROUP,ChatType.SUPERGROUP):
        if not is_group_admin(uid,chat.id): await update.message.reply_text("فقط مدیر"); return
        try:
            await context.bot.send_message(uid,f"📋 {chat.title}\n{await build_stats(chat.id)}",parse_mode="Markdown")
            await update.message.reply_text("✅ پیوی")
        except: await update.message.reply_text("اول /start در پیوی")
        return
    if low=="لیست سکوت" and chat.type in (ChatType.GROUP,ChatType.SUPERGROUP):
        lines=["🔇\n"]+[f"• `{u}`" for u in data.get("mute_list",{}).get(str(chat.id),{})]
        if len(lines)==1: lines.append("خالی")
        await update.message.reply_text("\n".join(lines),parse_mode="Markdown"); return
    if low in ("قفل گروه","قفل") and chat.type in (ChatType.GROUP,ChatType.SUPERGROUP) and is_group_admin(uid,chat.id):
        await update.message.reply_text("🔒" if await lock_group(context.bot,chat.id) else "❌"); return
    if low in ("برداشتن قفل","رفع قفل") and chat.type in (ChatType.GROUP,ChatType.SUPERGROUP) and is_group_admin(uid,chat.id):
        await update.message.reply_text("🔓" if await unlock_group(context.bot,chat.id) else "❌"); return
    if any(w in text for w in ("زمان","ساعت","تاریخ")): await update.message.reply_text(get_time_tehran()); return
    if any(w in text for w in ("جوک","جک","طنز")): await update.message.reply_text(f"😂 {await generate_joke()}"); return
    if any(text.startswith(t) for t in ("آب‌وهوا","آب و هوا","weather")):
        city=re.sub(r'^(آب[‌ ]?وهوا|weather)\s*','',text,flags=re.I).strip() or "تهران"
        await update.message.reply_text(get_weather(city),parse_mode="Markdown"); return
    if text.startswith("استیکر"):
        st=text.replace("استیکر","").strip() or "سلام"
        try:
            await context.bot.send_document(uid,InputFile(create_sticker_image(st[:16]),"sticker.webp"),caption=f"🎨 {st[:16]}")
        except: await update.message.reply_text("خطا")
        return
    if low in ("ربات","بات","bot","هی ربات"):
        bot=await context.bot.get_me()
        await update.message.reply_text(f"جانم؟ 😊 @{bot.username}\n{BOT_VERSION}"); return

    waiting=context.user_data.get("waiting")
    if waiting=="report_bug":
        context.user_data["waiting"]=None
        try:
            await context.bot.send_message(OWNER_ID,f"🐛 {user.full_name} `{uid}`\n{text}",parse_mode="Markdown")
            await update.message.reply_text("✅ ارسال شد")
        except: await update.message.reply_text("خطا")
        return
    if waiting=="ai_image":
        context.user_data["waiting"]=None
        await update.message.reply_text("🎨 در حال ساخت عکس...")
        try:
            en=await translate_to_en(text)
            url=ai_image_url(en)
            await update.message.reply_photo(url, caption=f"🖼 {text[:100]}")
        except Exception as e:
            await update.message.reply_text(f"خطا در ساخت عکس: {e}")
        return
    if waiting=="add_filter_info" and is_filter_manager(uid):
        parts=[p.strip() for p in text.split("|")]
        if len(parts)!=4: await update.message.reply_text("کشور | قیمت | حجم | مدت"); return
        context.user_data["new_filter"]={"country":parts[0],"price":parts[1],"volume":parts[2],"duration":parts[3],"file_id":None}
        context.user_data["waiting"]="add_filter_file"; await update.message.reply_text("✅ فایل را بفرست"); return
    if waiting=="weather":
        context.user_data["waiting"]=None; await update.message.reply_text(get_weather(text),parse_mode="Markdown"); return
    if waiting=="math":
        context.user_data["waiting"]=None; await update.message.reply_text(await ai_reply(uid,f"حل کن:\n{text}")); return
    if waiting=="sticker":
        context.user_data["waiting"]=None
        try: await context.bot.send_document(uid,InputFile(create_sticker_image(text[:16]),"sticker.webp"),caption=f"🎨 {text[:16]}")
        except: await update.message.reply_text("خطا")
        return
    if waiting=="addadmin" and is_owner(uid):
        context.user_data["waiting"]=None
        try:
            nid=int(text); data.setdefault("admins",[])
            if nid not in data["admins"] and nid!=OWNER_ID: data["admins"].append(nid); save_data(data); await update.message.reply_text(f"✅ {nid}")
            else: await update.message.reply_text("قبلاً")
        except: await update.message.reply_text("آیدی نامعتبر")
        return
    if waiting=="broadcast" and is_owner(uid):
        context.user_data["waiting"]=None; ok=fail=0
        for u in data.get("users",[]):
            try: await context.bot.send_message(u,f"📢\n{text}"); ok+=1
            except: fail+=1
        for g in data.get("groups",[]):
            try: await context.bot.send_message(int(g),f"📢\n{text}"); ok+=1
            except: fail+=1
        await update.message.reply_text(f"✅{ok} ❌{fail}"); return

    if chat.type in (ChatType.GROUP,ChatType.SUPERGROUP) and update.message.reply_to_message and is_group_admin(uid,chat.id):
        target=update.message.reply_to_message.from_user; tid=target.id
        if text in ("تنظیم مدیر","تنظیم مدیر ربات"):
            g=str(chat.id); data.setdefault("group_admins",{}).setdefault(g,[])
            if str(tid) not in data["group_admins"][g]: data["group_admins"][g].append(str(tid)); save_data(data); await update.message.reply_text(f"✅ {target.full_name}")
            else: await update.message.reply_text("قبلاً")
            return
        if text=="سکوت" or text.startswith("سکوت "):
            minutes=0; parts=text.split()
            if len(parts)==2 and parts[1].isdigit(): minutes=int(parts[1])
            await update.message.reply_text("🔇" if await mute_user(context.bot,chat.id,tid,minutes=minutes,by_id=uid) else "❌"); return
        if text in ("حذف سکوت","رفع سکوت"):
            await update.message.reply_text("🔊" if await unmute_user(context.bot,chat.id,tid) else "❌"); return
        if text in ("اخطار","warn"):
            g=str(chat.id); data.setdefault("warnings",{}).setdefault(g,{})
            data["warnings"][g][str(tid)]=data["warnings"][g].get(str(tid),0)+1; cnt=data["warnings"][g][str(tid)]; save_data(data)
            await update.message.reply_text(f"⚠️ {cnt}/3")
            if cnt>=3:
                try: await context.bot.ban_chat_member(chat.id,tid); data["warnings"][g][str(tid)]=0; save_data(data); await update.message.reply_text("🚫")
                except Exception as e: await update.message.reply_text(str(e))
            return
        if text in ("اخراج","kick","بن"):
            try: await context.bot.ban_chat_member(chat.id,tid); await update.message.reply_text(f"🚫 {target.full_name}")
            except Exception as e: await update.message.reply_text(str(e))
            return
        if text=="پاکسازی":
            msg=await update.message.reply_text("⏳"); deleted=0
            for i in range(1,151):
                try: await context.bot.delete_message(chat.id,update.message.message_id-i); deleted+=1
                except: pass
            try: await msg.edit_text(f"✅ {deleted}")
            except: pass
            return

    should_reply=True
    if chat.type in (ChatType.GROUP,ChatType.SUPERGROUP):
        bot=await context.bot.get_me(); uname=(bot.username or "").lower()
        mentioned=f"@{uname}" in low
        called=any(w in text for w in ("ربات","بات","bot","sibill"))
        reply_to_me=update.message.reply_to_message and update.message.reply_to_message.from_user and update.message.reply_to_message.from_user.id==bot.id
        gs=get_gs(chat.id)
        if gs.get("silent") and not is_group_admin(uid,chat.id): should_reply=False
        elif gs.get("only_admin") and not is_group_admin(uid,chat.id): should_reply=False
        elif gs.get("free_chat",True):
            if not (mentioned or called or reply_to_me):
                if not (len(text)<80 and ("؟" in text or "?" in text or any(w in low for w in ("چطوری","خوبی","سلام","درود","چه خبر")))):
                    should_reply=False
        elif not (mentioned or called or reply_to_me): should_reply=False
    if not should_reply: return

    quiet=get_gs(chat.id).get("quiet",False) if chat.type in (ChatType.GROUP,ChatType.SUPERGROUP) else False
    reply=await ai_reply(uid,text,quiet=quiet)
    if any(p in reply for p in ("متوجه نشدم","نمی‌فهمم")) or len(reply)<10:
        try: await context.bot.send_message(OWNER_ID,f"❓ {user.full_name} `{uid}`\n{text}",parse_mode="Markdown")
        except: pass
        reply="متأسفم، متوجه نشدم 😅"
    await update.message.reply_text(reply)

async def track_member(update, context):
    r=update.chat_member
    if not r: return
    chat=r.chat; chat_id=str(chat.id); old,new=r.old_chat_member.status,r.new_chat_member.status; user=r.new_chat_member.user
    bot=await context.bot.get_me()
    if user.id==bot.id and new in (ChatMemberStatus.MEMBER,ChatMemberStatus.ADMINISTRATOR):
        register_group(chat.id)
        try:
            for a in await context.bot.get_chat_administrators(chat.id):
                if a.status in ("creator",ChatMemberStatus.OWNER): data.setdefault("group_owners",{})[chat_id]=str(a.user.id)
                elif a.status in ("administrator",ChatMemberStatus.ADMINISTRATOR) and not a.user.is_bot:
                    data.setdefault("group_admins",{}).setdefault(chat_id,[])
                    if str(a.user.id) not in data["group_admins"][chat_id]: data["group_admins"][chat_id].append(str(a.user.id))
            save_data(data)
        except: pass
        try:
            await context.bot.send_message(chat.id,f"سلام! من @{bot.username}\n**{BOT_VERSION}**\nبگو **ربات** یا **پنل**",parse_mode="Markdown")
        except: pass
        return
    if new in (ChatMemberStatus.MEMBER,ChatMemberStatus.ADMINISTRATOR) and old in (ChatMemberStatus.LEFT,ChatMemberStatus.BANNED):
        data.setdefault("member_count",{})[chat_id]=data.get("member_count",{}).get(chat_id,0)+1
        if r.from_user and r.from_user.id!=user.id:
            inv=str(r.from_user.id)
            data.setdefault("invite_count",{}).setdefault(chat_id,{})
            data["invite_count"][chat_id][inv]=data["invite_count"][chat_id].get(inv,0)+1
        save_data(data)
        if get_gs(chat.id).get("welcome",True) and not user.is_bot:
            try: await context.bot.send_message(chat.id,f"سلام {user.first_name or 'دوست'}! 🌟")
            except: pass
    if new in (ChatMemberStatus.LEFT,ChatMemberStatus.BANNED) and old in (ChatMemberStatus.MEMBER,ChatMemberStatus.ADMINISTRATOR):
        data.setdefault("left_members",{})[chat_id]=data.get("left_members",{}).get(chat_id,0)+1
        data.setdefault("member_count",{})[chat_id]=max(0,data.get("member_count",{}).get(chat_id,1)-1); save_data(data)

async def post_init(app):
    await app.bot.set_my_commands([BotCommand("start","شروع"),BotCommand("panel","پنل")])
    bot=await app.bot.get_me(); msg=f"🟢 @{bot.username}\n{BOT_VERSION}"
    for u in data.get("users",[]):
        try: await app.bot.send_message(u,msg)
        except: pass
        await asyncio.sleep(0.03)
    for g in data.get("groups",[]):
        try: await app.bot.send_message(int(g),msg)
        except: pass
        await asyncio.sleep(0.03)

def main():
    for k,v in DEFAULT.items():
        if k not in data: data[k]=v
    save_data(data)
    app=Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("panel",open_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ChatMemberHandler(track_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO|filters.VIDEO|filters.Document.ALL, handle_message))
    print(f"🤖 {BOT_VERSION} آماده...")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message","callback_query","chat_member","my_chat_member"])

if __name__=="__main__":
    main()
