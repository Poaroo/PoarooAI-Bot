# PoarooAI Bot

**Version 1.0 — AiSecuredByPoaroo4**  
Design By Poaroo — به امید آزادی ایران

ربات تلگرام هوشمند: بخش دانش‌آموز پایه‌های ۱ تا ۱۲، تحلیل عکس و PDF، کوین، چند نقش.

## متغیرهای محیطی (Secrets)

- `TELEGRAM_TOKEN` — توکن ربات از @BotFather  
- `GROQ_API_KEY` — کلید از https://console.groq.com/keys  
- `OWNER_ID` — آیدی عددی تلگرام مالک (اختیاری)

## اجرای محلی

```bash
pip install -r requirements.txt
export TELEGRAM_TOKEN=...
export GROQ_API_KEY=...
python bot.py
```

## استقرار ۲۴ ساعته با GitHub + Railway

1. این پوشه را روی GitHub Push کنید  
2. در [railway.app](https://railway.app) با GitHub وارد شوید  
3. New Project → Deploy from GitHub Repo  
4. Variables را اضافه کنید  
5. Deploy — ربات آنلاین می‌ماند  

همین کار با Render.com (Background Worker) هم ممکن است.
