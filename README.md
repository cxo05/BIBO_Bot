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
#Create .env variables
cat > .env << EOF
bot_key=_INSERTKEYHERE_
databasePath=bibo.db
EOF
#Install packages
pip install -r requirements.txt
#Running the bot
py biboBot.py
```

#Deployment to raspberry pi

Learning materials:

* [Raspberrypi Networking](https://raspberrypi.stackexchange.com/questions/37920/how-do-i-set-up-networking-wifi-static-ip-address-on-raspbian-raspberry-pi-os/37921#37921)
* [Systemd](https://github.com/torfsen/python-systemd-tutorial)

```bash
#Connect to pi assuming its already setup
ssh pi@IP_ADDRESS
#Change network if necessary
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
#Same as development
git clone https://github.com/2x0c0h1/BIBO_Bot.git
...
...
#Copy bibo.service to /etc/systemd/system
cp bibo.service /etc/systemd/system
#Reload
systemctl daemon-reload
#Enable autorun on boot
systemctl enable bibo
#Check/debug service
systemctl status bibo
```
