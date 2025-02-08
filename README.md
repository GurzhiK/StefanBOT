Here’s a more concise version of the `README.md`:

```markdown
# StefanBot - Django & Telegram Bot

A Django project integrated with a Telegram bot (`StefanBot.py`).

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/GuzhiK/StefanBot.git
   cd StefanBot
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add Telegram bot token:**
   Create a `.env` file:
   ```plaintext
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

## Run Django

1. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

2. **Start the server:**
   ```bash
   python manage.py runserver
   ```

   Access at `http://127.0.0.1:8000/`.

## Run Telegram Bot

```bash
python StefanBot.py
```

Interact with your bot on Telegram.
