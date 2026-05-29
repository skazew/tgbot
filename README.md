# Telegram-бот «Вікторина для перевірки знань»

## 1. Опис

Telegram-бот для перевірки знань студентів у форматі вікторини з вибором однієї правильної відповіді. Призначений як інструмент експрес-самоконтролю : студент обирає дисципліну, бот по одному надсилає випадкові питання з підготовленої бази, фіксує результат і веде статистику.

## 2. Технологічний стек

- Python 3.11+
- aiogram 3.4+ (async)
- SQLAlchemy 2.0 (async) + aiosqlite
- SQLite (файл `quiz_bot.db`)
- Alembic — міграції БД
- python-dotenv — змінні оточення
- pytest + pytest-asyncio — тести
- стандартний `logging`

## 3. Структура проєкту

```
quiz_bot/
├── bot.py                  # точка входу
├── config.py               # завантаження .env, константи
├── .env.example
├── .gitignore
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
├── database/
│   ├── engine.py           # async engine + sessionmaker + init_db
│   ├── models.py           # ORM-моделі (User, Discipline, Question, Answer, Attempt)
│   └── repositories.py     # репозиторії
├── handlers/
│   ├── start.py            # /start, /help, /cancel
│   ├── quiz.py             # /quiz + FSM вікторини
│   ├── stats.py            # /stats + рейтинг
│   └── admin.py            # /admin + CRUD + /stats_all + /export
├── services/
│   ├── quiz_service.py     # calculate_percentage, select_questions
│   └── stats_service.py    # агрегатори статистики
├── keyboards/
│   ├── user_kb.py
│   └── admin_kb.py
├── states/
│   ├── quiz_states.py      # QuizStates
│   └── admin_states.py     # AddQuestionStates тощо
├── utils/
│   ├── validators.py       # validate_question_text/answer_text/discipline_name
│   └── csv_export.py
├── tests/
│   ├── conftest.py
│   ├── test_quiz_service.py
│   ├── test_repositories.py
│   └── test_validators.py
└── scripts/
    └── seed_data.py        # python -m scripts.seed_data
```

## 4. Встановлення

1) Клонування репозиторію:

```bash
git clone <url>
cd quiz_bot
```

2) Створення та активація віртуального середовища:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

3) Встановлення залежностей:

```bash
pip install -r requirements.txt
```

4) Реєстрація бота в Telegram:
- Відкрийте чат із [@BotFather](https://t.me/BotFather).
- Команда `/newbot`, далі введіть назву та username.
- Отримайте токен виду `123456:ABC-XYZ`.

5) Налаштування `.env`:

```bash
cp .env.example .env   # Linux/macOS
copy .env.example .env # Windows
```

Заповніть значення:

```
BOT_TOKEN=ваш_токен_від_BotFather
DATABASE_URL=sqlite+aiosqlite:///./quiz_bot.db
ADMIN_IDS=ваш_telegram_id,ще_один_id
QUIZ_LENGTH=10
LOG_LEVEL=INFO
```

6) Міграції:

```bash
alembic upgrade head
```

7) Наповнення тестовими даними (3 дисципліни × 10 питань):

```bash
python -m scripts.seed_data
```

8) Запуск:

```bash
python bot.py
```

## 5. Як стати адміністратором

Щоб отримати доступ до адмін-меню (команда `/admin`), додайте свій `telegram_id` (отримати можна, наприклад, через [@userinfobot](https://t.me/userinfobot)) у змінну `ADMIN_IDS` файла `.env` (через кому, якщо адмінів кілька), і перезапустіть бота. Після команди `/start` ваш запис у БД буде підвищено до ролі `admin` автоматично.

## 6. Тести

```bash
pytest -v
```

Тести використовують in-memory SQLite (`sqlite+aiosqlite:///:memory:`). Покриваються: `quiz_service` (підрахунок відсотка, вибір випадкових питань), репозиторії (`UserRepository.get_or_create`, `DisciplineRepository`, `QuestionRepository` + `selectinload`), валідатори (межі довжини).

## 7. Розгортання на VPS через systemd

Приклад юніт-файлу `/etc/systemd/system/quiz-bot.service`:

```ini
[Unit]
Description=Telegram Quiz Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/quiz_bot
EnvironmentFile=/opt/quiz_bot/.env
ExecStart=/opt/quiz_bot/.venv/bin/python /opt/quiz_bot/bot.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Активація:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now quiz-bot
sudo systemctl status quiz-bot
journalctl -u quiz-bot -f
```

## 8. Команди бота

Для користувачів:
- `/start` — реєстрація і головне меню
- `/help` — довідка
- `/quiz` — обрати дисципліну і розпочати вікторину
- `/stats` — статистика проходжень
- `/rating` — рейтинг за дисципліною
- `/cancel` — перервати вікторину

Для адміністраторів:
- `/admin` — головне адмін-меню
- `/stats_all` — зведена статистика
- `/export` — експорт усіх спроб у CSV

## 9. Припущення та зауваження

- FSM-storage — `MemoryStorage`. Для продакшну рекомендовано Redis (`aiogram.fsm.storage.redis.RedisStorage`).
- БД — SQLite (відповідно до ТЗ дипломної роботи). Для високих навантажень — мігрувати на PostgreSQL.
- Форматування Telegram-повідомлень — HTML (`<b>...</b>`).

