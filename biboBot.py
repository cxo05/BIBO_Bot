from dotenv import load_dotenv
load_dotenv()

import os
botKey = os.environ.get("bot_key") #Create a .env file in root folder with bot_key=INSERTKEYHERE
databasePath = os.environ.get("databasePath") #Create new line with databasePath=INSERTDATABASEPATHHERE
import sqlite3
import logging
from sqlite3 import Error
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters
)
from telegram import File
from math import sin, cos, sqrt, atan2, radians
from datetime import datetime

#Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def connect_database(file):
    #Connect to database
    conn = None
    try:
        conn = sqlite3.connect(file)
        return conn
    except Error as e:
        logger.error(e)
    return conn

def execute_sql(conn, sql):
    #Excutes sql queries
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        logger.error(e)

def checkInOut(update,context):
    #TODO
    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")

    context.bot.send_message(chat_id=update.effective_chat.id, text="Pls type your rank and name")
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, addname))

def addUser(update,context):
    #TODO Instead of one line input, split inputs into mulitple bot prompts for user data
    telegram_id = update.message.chat_id
    full_name = context.args[0]
    masked_nric = context.args[1]
    company_id = context.args[2]

    conn = connect_database(databasePath)

    if conn is not None:
        sql = ('INSERT INTO user (telegram_id,full_name,masked_nric,company_id,isAdmin) VALUES (?,?,?,?,?)', [telegram_id, full_name, masked_nric, company_id])
        execute_sql(conn, sql)
        update.message.send_message(chat_id=update.effective_chat.id, text="You have been added to the database")
    else:
        logger.error("Error Adding User")


def authenticate(update,context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Send your location pls")
    dispatcher.add_handler(MessageHandler(Filters.location & ~Filters.command,authenticatedd))

def authenticatedd(update,context):
    print("authenticatedist running")
    local=update.message.location
    local1=str(local)
    local2=""
    for number in local1:
        if number in "0123456789. ":
            local2= local2 + number
    places=local2.split(" ")


    #Calculation for distance between two points
    R = 6373.0

    lat1 = radians(float(places[3]))
    lon1 = radians(float(places[1]))
    lat2 = radians(1.4248641143077456)
    lon2 = radians(103.82664614345568)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    #Changing radius from a point in camp to register too far or near
    if distance>5:
        context.bot.send_message(chat_id=update.effective_chat.id, text='''Authentication failed, pls move
        closer to camp and resend your location''')
        location(update,context)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Authentication succesful")
        checkin(update,context)

    return 0


if __name__=="__main__":
    sql_create_company_table = """ CREATE TABLE IF NOT EXISTS company (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        name text NOT NULL
                                    ); """

    sql_create_user_table = """CREATE TABLE IF NOT EXISTS user (
                                    telegram_id integer PRIMARY KEY,
                                    full_name text NOT NULL,
                                    masked_nric text NOT NULL,
                                    isAdmin integer DEFAULT 0,
                                    company_id integer NOT NULL,
                                    FOREIGN KEY (company_id) REFERENCES company (id)
                                );"""

    sql_create_timesheet_table = """CREATE TABLE IF NOT EXISTS timesheet (
                                    id integer PRIMARY KEY AUTOINCREMENT,
                                    telegram_id integer NOT NULL,
                                    time text NOT NULL,
                                    status integer NOT NULL,
                                    FOREIGN KEY (telegram_id) REFERENCES user (telegram_id)
                                );"""

    #Connect to database
    conn = connect_database(databasePath)

    if conn is not None:
        execute_sql(conn, sql_create_company_table)
        execute_sql(conn, sql_create_user_table)
        execute_sql(conn, sql_create_timesheet_table)

    #define telegram bot
    updater = Updater(token=botKey, use_context=True)

    #adding handlers to telegram bot
    dispatcher=updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("join", addUser)))
    dispatcher.add_handler(CommandHandler("checkInOut", checkInOut)))


    #start telegram bot
    updater.start_polling()
    logger.info("Bot Running")
    #standby mode for telegram bot
    updater.idle()
