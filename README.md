
# Webhook-бот для Render (бесплатный Web Service)

## Деплой
1) Залейте файлы в GitHub-репозиторий (main.py, config.py, requirements.txt, Procfile, assets/price.pdf).
2) Render → New → Web Service → выберите репозиторий.
3) Build: `pip install -r requirements.txt`
   Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4) Environment:
   - BOT_TOKEN = токен бота
   - PUBLIC_CHANNEL_USERNAME = ai_do_after
   - PDF_PATH = assets/price.pdf
   - WEBHOOK_SECRET = ai123secret (или свой)
5) После первого деплоя Render даст адрес `https://xxx.onrender.com`.
   Добавьте переменную BASE_URL = этот адрес → Redeploy.
6) Проверка: `GET /ping` → {"ok": true}
   В Telegram: /start site → работает меню, «Прайс (PDF)», /id.
