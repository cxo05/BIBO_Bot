# BIBO_Bot
BIBO Tracking and other functionalities using Telegram

BIBO_Bot uses [Python](https://www.python.org/) for the backend logic and [SQLite](https://www.sqlite.org/index.html) for the database. We may improve the database when required.
# Development

Requirements :

* [Python](https://nodejs.org/en/)
* [SQLite](https://www.sqlite.org/index.html)
* Telegram Bot Key

```bash
#Clone project
git clone https://github.com/2x0c0h1/BIBO_Bot.git
cd BIBO_Bot
#Create .env file and add keys
echo bot_key=_INSERTKEYHERE_ >> .env
echo databasePath=bibo.db >> .env
#Install packages
pip install -r requirements.txt
#Running the bot
py biboBot.py
#Autoreloading during development
./autoreload py biboBot.py
```
