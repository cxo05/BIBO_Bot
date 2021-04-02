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
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    Filters
)
from telegram import ReplyKeyboardMarkup
from math import sin, cos, sqrt, atan2, radians
from datetime import datetime

#Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

BIBO, LOCATION = range(2)

def connect_database(file):
    #Connect to database
    conn = None
    try:
        conn = sqlite3.connect(file)
        return conn
    except Error as e:
        logger.error(e)
    return conn

def execute_sql(conn, sql, args=None):
    #Excutes sql queries
    try:
        c = conn.cursor()
        c.execute(sql, args)
        conn.commit()
        return c
    except Error as e:
        logger.error(e)

def help(update, context):
    context.bot.send_message(
        update.effective_chat.id,
        '1) To join a company/battery.\n' +
        '   /join FULL_NAME COMPANY_NAME\n' +
        '2) To create a company/battery.\n' +
        '   /create_company COMPANY_NAME\n' +
        '3) To check in or out /checkInOut'
    )

def addUser(update, context):
    try:
        telegram_id = update.message.chat_id
        full_name = context.args[0]
        company_name = context.args[1]
    except Exception as e:
        logger.error(e)
        context.bot.send_message(update.effective_chat.id, "/join FULL_NAME COMPANY_NAME")
        return

    conn = connect_database(databasePath)

    if conn is not None:
        sql = 'INSERT INTO user (telegram_id,full_name,company_id) VALUES (?,?, (SELECT id from company WHERE name = (?)))'
        args = (telegram_id, full_name, company_name)
        execute_sql(conn, sql, args)
        context.bot.send_message(update.effective_chat.id, "You have been added to the database")
    else:
        logger.error("Error Adding User")

def setAdmin(update, context):
    if(context.args[0] == "password"):
        telegram_id = update.message.chat_id
        conn = connect_database(databasePath)

        if conn is not None:
            sql = 'UPDATE user SET isAdmin = 1 WHERE telegram_id = (?)'
            args = (telegram_id,)
            execute_sql(conn, sql, args)
            context.bot.send_message(update.effective_chat.id, "You are now an admin")
        else:
            logger.error("Error Changing to Admin")
    else:
        context.bot.send_message(update.effective_chat.id, "Wrong password")

def addCompany(update, context):
    conn = connect_database(databasePath)
    telegram_id = update.message.chat_id
    company_name = context.args[0]

    if conn is not None:
        sql_1 = 'SELECT isAdmin FROM user WHERE telegram_id = (?)'
        args_1 = (telegram_id,)
        if(execute_sql(conn, sql_1, args_1).fetchall() == 0):
            context.bot.send_message(update.effective_chat.id, "You are not an admin")
            return
        sql_2 = 'INSERT INTO company (company_name) VALUES (?)'
        args_2 = (company_name,)
        execute_sql(conn, sql_2, args_2)
        context.bot.send_message(update.effective_chat.id, "Added company to the database")
    else:
        logger.error("Error Adding Company")

def checkInOut(update, context):
    keyboard = [['Book In', 'Book Out']]
    update.message.reply_text('Select Option:', reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return BIBO

def authenticate(update, context):
    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")

    if(update.message.text == "Book In"):
        update.message.reply_text("Send your location")
        return LOCATION
    else:
        update.message.reply_text("Book Out") #TODO Book out

def authenticatedd(update, context):
    #asd
    local = update.message.location
    logger.info(
        "Location: %f / %f", local.latitude, local.longitude
    )
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
        context.bot.send_message(chat_id=update.effective_chat.id, text='''Location check failed, pls move
        closer to camp and resend your location''')
        location(update,context)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Location sent successfully")
        checkin(update,context)

    return 0

def cancel(update, context):
    update.message.reply_text('BIBO operation canceled')
    return ConversationHandler.END

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
        execute_sql(conn, sql_create_company_table, ())
        execute_sql(conn, sql_create_user_table, ())
        execute_sql(conn, sql_create_timesheet_table, ())

    #define telegram bot
    updater = Updater(token=botKey, use_context=True)

    #adding handlers to telegram bot
    dispatcher=updater.dispatcher
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("join", addUser))
    dispatcher.add_handler(CommandHandler("setAdmin", setAdmin))
    dispatcher.add_handler(CommandHandler("create_company", addCompany))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("checkInOut", checkInOut)],
        states={
            BIBO: [MessageHandler(Filters.regex('^(Book In|Book Out)$'), authenticate)],
            LOCATION: [
                MessageHandler(Filters.location, authenticatedd),
            ]
        },
        fallbacks=[MessageHandler(Filters.text & ~Filters.command, cancel)]
    )
    dispatcher.add_handler(conv_handler)

    #start telegram bot
    updater.start_polling()
    logger.info("Bot Running")
    #standby mode for telegram bot
    updater.idle()
