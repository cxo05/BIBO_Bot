# HA_Bot
HA Tracking and other functionalities using Telegram

HA_Bot uses [node.js](https://nodejs.org/en/) for the backend logic and [SQLite](https://www.sqlite.org/index.html) for the database. We may improve the database when required. 
# Development 

Requirements :

* [Node.js](https://nodejs.org/en/)
* [SQLite](https://www.sqlite.org/index.html)
* Telegram Bot Key

```bash
#Clone project
git clone https://github.com/2x0c0h1/HA_Bot.git
cd HA_Bot
#Create .env file and add key
echo bot_key=_INSERTKEYHERE_ > .env
# install necessary packages from (package.json)
npm install
# run bot
node server.js
```

