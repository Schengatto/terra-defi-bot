#Overview
Python services folder.

#Run all services with docker compose
Execute the following command on the system terminal
```
docker-compose up -d
```

#Configuration
Secrets are not tracked. Before building the images:
- copy every `services/*/settings/telegram_conf/*.conf.example` to the same name without `.example` and fill in the Telegram bot token and chat id
- export `EMAIL_PASSWORD` (SMTP password of the sender account) and, optionally, `TERRA_POSTGRES_PASSWORD` / `TEST_TERRA_POSTGRES_PASSWORD`
