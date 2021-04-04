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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

SAVE_NAME, SAVE_COMPANY, COMPANY_NAME, BIBO, LOCATION = range(5)

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
        '   /join\n' +
        '2) To create a company/battery.\n' +
        '   /create_company\n' +
        '3) To book in or out\n' +
        '   /bookInOut'
    )

def saveUserName(update, context):
    update.message.reply_text("Enter your name")
    return SAVE_NAME

def saveUserCompany(update, context):
    context.user_data["name"] = update.message.text
    update.message.reply_text("Enter company/battery name")
    return SAVE_COMPANY

def addUser(update, context):
    conn = connect_database(databasePath)
    telegram_id = update.message.chat_id
    sql = 'INSERT INTO user (telegram_id,full_name,company_id) VALUES (?,?, (SELECT id from company WHERE name = (?)))'
    args = (telegram_id, context.user_data["name"], update.message.text)
    execute_sql(conn, sql, args)
    update.message.reply_text(context.user_data["name"] + " has been added to " + update.message.text)
    return ConversationHandler.END

def setAdmin(update, context):
    if(context.args[0] == "password"):
        telegram_id = update.message.chat_id
        conn = connect_database(databasePath)
        sql = 'UPDATE user SET isAdmin = 1 WHERE telegram_id = (?)'
        args = (telegram_id,)
        execute_sql(conn, sql, args)
        update.message.reply_text("You are now an admin")
    else:
        update.message.reply_text("Wrong password")

def addCompanyMsg(update, context):
    conn = connect_database(databasePath)
    sql = 'SELECT isAdmin FROM user WHERE telegram_id = (?)'
    args = (update.message.chat_id,)
    asd = execute_sql(conn, sql, args).fetchone()
    if(asd[0] == 1):
        update.message.reply_text("Enter company/battery name")
        return COMPANY_NAME
    else:
        update.message.reply_text("You are not an admin")
        return ConversationHandler.END

def addCompany(update,context):
    conn = connect_database(databasePath)
    company_name = update.message.text
    sql = 'INSERT INTO company (name) VALUES (?)'
    args = (company_name,)
    execute_sql(conn, sql, args)
    update.message.reply_text("Added " + company_name + " to the database")
    return ConversationHandler.END

def InOutButton(update, context):
    keyboard = [['Book In', 'Book Out']]
    update.message.reply_text('Select Option:', reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return BIBO

def authenticateLocation(update, context):
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
        update.message.reply_text("Too far from camp, move closer and resend your location")
        return LOCATION
    else:
        conn = connect_database(databasePath)
        update.message.reply_text("Location valid")
        #status is a bool (0 = Book in, 1 = Book out)
        sql = 'INSERT INTO timesheet (telegram_id, time_in) VALUES (?,?)'
        args = (update.message.chat_id, datetime.now())
        execute_sql(conn, sql, args)
        update.message.reply_text("You have booked in")

def bookIn(update, context):
    update.message.reply_text("Send your location")
    return LOCATION

def bookOut(update, context):
    conn = connect_database(databasePath)
    #status is a bool (0 = Book in, 1 = Book out)
    sql = 'UPDATE timesheet SET time_out = (?) WHERE telegram_id = (?) AND time_out = NULL ORDER BY datetime(time_in) DESC LIMIT 1'
    args = (datetime.now(), update.message.chat_id)
    execute_sql(conn, sql, args)
    update.message.reply_text("You have booked out")

def cancel(update, context):
    update.message.reply_text('Current operation canceled')
    return ConversationHandler.END

if __name__=="__main__":
    sql_create_company_table = """ CREATE TABLE IF NOT EXISTS company (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        name text NOT NULL
                                    ); """

    sql_create_user_table = """CREATE TABLE IF NOT EXISTS user (
                                    telegram_id integer PRIMARY KEY,
                                    full_name text NOT NULL,
                                    isAdmin integer DEFAULT 0,
                                    company_id integer,
                                    FOREIGN KEY (company_id) REFERENCES company (id)
                                );"""

    sql_create_timesheet_table = """CREATE TABLE IF NOT EXISTS timesheet (
                                    id integer PRIMARY KEY AUTOINCREMENT,
                                    telegram_id integer NOT NULL,
                                    time_in text NOT NULL,
                                    time_out text,
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
    dispatcher.add_handler(CommandHandler("start", help))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("setAdmin", setAdmin))
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("create_company", addCompanyMsg),
            CommandHandler("bookInOut", InOutButton),
            CommandHandler("join", saveUserName),
        ],
        states={
            SAVE_NAME:[
                MessageHandler(Filters.text & ~Filters.command, saveUserCompany),
            ],
            SAVE_COMPANY:[
                MessageHandler(Filters.text & ~Filters.command, addUser),
            ],
            COMPANY_NAME: [
                MessageHandler(Filters.text & ~Filters.command, addCompany),
            ],
            BIBO: [
                MessageHandler(Filters.regex('^(Book In)$'), bookIn),
                MessageHandler(Filters.regex('^(Book Out)$'), bookOut),
            ],
            LOCATION: [
                MessageHandler(Filters.location, authenticateLocation),
            ]
        },
        fallbacks=[
            MessageHandler(Filters.text & ~Filters.command, cancel),
        ],
        allow_reentry=True
    )
    dispatcher.add_handler(conv_handler)

    #start telegram bot
    updater.start_polling()
    logger.info("Bot Running")
    #standby mode for telegram bot
    updater.idle()
