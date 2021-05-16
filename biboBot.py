from dotenv import load_dotenv
load_dotenv()

import os
botKey = os.environ.get("bot_key") #Create a .env file in root folder with bot_key=INSERTKEYHERE
databasePath = os.environ.get("databasePath") #Create new line with databasePath=INSERTDATABASEPATHHERE
from functools import wraps
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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from math import sin, cos, sqrt, atan2, radians
from datetime import datetime
import telegramcalendar

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

SAVE_NAME, SAVE_COMPANY, ADD_COMPANY, GET_USERS, VIEW_IN_CAMP, BIBO, LOCATION, VIEW_DATE_HISTORY = range(8)

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
    except Error:
        logger.exception("message")

def help(update, context):
    keyboard = [
        [InlineKeyboardButton("Book In", callback_data='Book In')],
        [InlineKeyboardButton("Book Out", callback_data='Book Out')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        update.effective_chat.id,
        '1) To join/update your name and company/battery.\n' +
        '   /join\n' +
        '2) Show users\n' +
        '   /getUsers\n' +
        '3) View your history\n' +
        '   /viewHistory\n'+
        '4) View others history\n' +
        '   /viewHistory NAME\n' +
        '5) View particular date\n' +
        '   /viewDateHistory\n' +
        '6) View people in camp\n' +
        '   /viewInCamp\n'+
        '7) /adminHelp'
        , reply_markup=reply_markup
    )
    return BIBO

def admin_restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        if "isadmin" not in context.user_data or context.user_data["isadmin"] == False:
            context.bot.send_message(update.effective_chat.id, 'You are not an admin')
            return
        return func(update, context, *args, **kwargs)
    return wrapped

@admin_restricted
def adminHelp(update, context):
    context.bot.send_message(
    update.effective_chat.id,
        '1) To create a company/battery.\n' +
        '   /create_company\n'
    )

def user_restricted(func):
    @wraps(func)
    def wrapped(update, context):
        conn = connect_database(databasePath)
        sql = 'SELECT EXISTS(SELECT 1 FROM user WHERE telegram_id=(?))'
        args = (update.effective_chat.id,)
        result = execute_sql(conn, sql, args).fetchone()
        if result==0:
            context.bot.send_message(update.effective_chat.id, 'Create user with /join first')
            return
        return func(update, context)
    return wrapped

def saveUserName(update, context):
    if "indatabase" in context.user_data:
        update.message.reply_text("You are already registered. You will now edit your details.")
    update.message.reply_text("Enter your name")
    return SAVE_NAME

def saveUserCompany(update, context):
    context.user_data["name"] = update.message.text
    update.message.reply_text("Enter company/battery name")
    return SAVE_COMPANY

def addUser(update, context):
    conn = connect_database(databasePath)
    telegram_id = update.message.chat_id
    sql = 'INSERT INTO user (full_name,company_id, telegram_id) VALUES (?, (SELECT id from company WHERE name = (?)), ?)'
    args = (context.user_data["name"], update.message.text, telegram_id)
    if("indatabase" in context.user_data):
        sql = 'UPDATE user SET full_name = (?), company_id = (SELECT id from company WHERE name = (?)) WHERE telegram_id = (?)'
    try:
        execute_sql(conn, sql, args)
    except Error as e:
        update.message.reply_text("Error occurred")
    else:
        update.message.reply_text(context.user_data["name"] + " has been added to " + update.message.text)
        context.user_data["indatabase"] = True
    return ConversationHandler.END

def setAdmin(update, context):
    if(context.args[0] == "password"):
        telegram_id = update.message.chat_id
        context.user_data["isadmin"] = True
        update.message.reply_text("You are now an admin")
    else:
        update.message.reply_text("Wrong password")

@admin_restricted
def addCompanyMsg(update, context):
    update.message.reply_text("Enter company/battery name")
    return ADD_COMPANY

def addCompany(update,context):
    conn = connect_database(databasePath)
    company_name = update.message.text
    sql = 'INSERT INTO company (name) VALUES (?)'
    args = (company_name,)
    try:
        execute_sql(conn, sql, args)
    except Error as e:
        update.message.reply_text("Error")
    else:
        update.message.reply_text("Added " + company_name + " to the database")
    return ConversationHandler.END

def authenticateLocation(update, context):
    local = update.message.location
    logger.info(
        "Location: %f / %f", local.latitude, local.longitude
    )
    live_period=local.live_period

    if live_period==None:
        update.message.reply_text("Send live location: ")
        return LOCATION
    else:
        #Calculation for distance between two points
        R = 6373.0

        lat1 = radians(float(local.latitude))
        lon1 = radians(float(local.longitude))
        lat2 = radians(1.4248641143077456)
        lon2 = radians(103.82664614345568)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

    #Checking distance
    if distance>0.2:
        update.message.reply_text("Too far from camp, move closer and resend your location")
        context.bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)
        return LOCATION
    else:
        conn = connect_database(databasePath)
        update.message.reply_text("Location valid")
        sql = 'INSERT INTO timesheet (telegram_id, time_in) VALUES (?,?)'
        args = (update.message.chat_id, datetime.now())
        execute_sql(conn, sql, args)
        update.message.reply_text("You have booked in.")
        context.bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)
        return ConversationHandler.END

def testbookIn(update, context):
    conn = connect_database(databasePath)
    update.message.reply_text("Location valid")
    sql = 'INSERT INTO timesheet (telegram_id, time_in) VALUES (?,?)'
    args = (update.message.chat_id, datetime.now())
    execute_sql(conn, sql, args)
    update.message.reply_text("You have booked in")

@user_restricted
def bookIn(update, context):
    context.bot.send_message(update.effective_chat.id, "Send your live location: ")
    return LOCATION

@user_restricted
def bookOut(update, context):
    conn = connect_database(databasePath)
    sql = 'UPDATE timesheet SET time_out = (?) WHERE id = (SELECT id FROM timesheet WHERE telegram_id = (?) ORDER BY time_in DESC LIMIT 1) AND time_out IS NULL'
    args = (datetime.now(), update.effective_chat.id)
    result = execute_sql(conn, sql, args)
    if(result.rowcount == 1):
        context.bot.send_message(update.effective_chat.id, "You have booked out")
    else:
        context.bot.send_message(update.effective_chat.id, "You have not booked in")

@user_restricted
def getUsersMsg(update, context):
    update.message.reply_text("Enter company/battery name")
    return GET_USERS

def getUsers(update, context):
    company_name = update.message.text
    conn = connect_database(databasePath)
    sql = 'SELECT full_name FROM user WHERE company_id = (SELECT id FROM company WHERE name = (?)) ORDER BY full_name ASC'
    args = (company_name,)
    results = execute_sql(conn, sql, args).fetchall()
    if(len(results) > 0):
        text = ""
        x = 0
        for row in results:
            x = x + 1
            text = text + str(x) + ". " + str(row[0]) + "\n"
        update.message.reply_text(text)
    else:
        update.message.reply_text("Company does not exist or is empty")
    return ConversationHandler.END

def viewUserHistory(update, context):
    telegram_id = update.message.chat_id
    conn = connect_database(databasePath)
    if(context.args):
        conn = connect_database(databasePath)
        sql = 'SELECT isAdmin FROM user WHERE telegram_id = (?)'
        args = (update.message.chat_id,)
        asd = execute_sql(conn, sql, args).fetchone()
        if(asd[0] == 1):

            sql_1 = 'SELECT telegram_id FROM user WHERE full_name = (?)'
            args_1=""
            for i in range(len(context.args)):
                args_1=args_1+str(context.args[i])+" "
            args_1=(args_1[0:-1],)
            telegram_id = execute_sql(conn, sql_1, args_1).fetchone()[0]
            logger.info(telegram_id)
        else:
            update.message.reply_text("You are not an admin")
            return ConversationHandler.END

    sql = 'SELECT time_in, time_out FROM timesheet WHERE telegram_id = (?)'
    args = (telegram_id,)
    results = execute_sql(conn, sql, args).fetchall()
    #TODO Make this a navigatable list using inlinekeyboard or think of a better way to view lesser data
    if(results):
        text = ""
        for row in results:
            text = text + "In: " + datetime.fromisoformat(row[0]).strftime("%d-%m-%Y %H%M") + "hrs\n" + "Out: " + (datetime.fromisoformat(row[1]).strftime("%d-%m-%Y %H%M") + "hrs \n\n" if isinstance(row[1], str) else "\n\n")
        update.message.reply_text(text)
    return ConversationHandler.END

@user_restricted
def viewInCampMsg(update, context):
    update.message.reply_text("Enter company/battery name")
    return VIEW_IN_CAMP

def viewInCamp(update, context):
    conn = connect_database(databasePath)
    company_name = update.message.text
    sql = 'SELECT id FROM company WHERE name = (?)'
    args = (company_name,)
    results = execute_sql(conn, sql, args).fetchone()
    if results is None:
        update.message.reply_text("Company/Battery does not exist")
        return ConversationHandler.END
    sql_1 = """
            SELECT
                user.full_name
            FROM
                (SELECT telegram_id AS t_id, max(id) AS max_id, time_out AS out FROM timesheet GROUP BY telegram_id)
            INNER JOIN
                user ON (user.telegram_id = t_id)
            WHERE out IS NULL AND user.company_id = (?)
            ORDER BY user.full_name
        """
    args_1 = (results[0],)
    results = execute_sql(conn, sql_1, args_1).fetchall()
    if (len(results) == 0):
        update.message.reply_text("No one in camp")
    else:
        text = ""
        for index, user in enumerate(results, start=1):
            text = text + str(index) + ". " + user[0] + "\n"
        update.message.reply_text(text)

@user_restricted
def getDate(update, context):
    update.message.reply_text("Please select a date: ", reply_markup=telegramcalendar.create_calendar())
    return VIEW_DATE_HISTORY

def viewDateHistory(update, context):
    selected,date = telegramcalendar.process_calendar_selection(update, context)
    if selected:
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="You selected %s" % (date.strftime("%d/%m/%Y")),
                        reply_markup=ReplyKeyboardRemove())
    date = date.strftime("%Y-%m-%d")
    conn = connect_database(databasePath)
    sql = '''
        SELECT user.full_name, timesheet.time_in, timesheet.time_out FROM timesheet LEFT JOIN user ON timesheet.telegram_id = user.telegram_id WHERE date(timesheet.time_in) = (?) OR date(timesheet.time_out) = (?)
        UNION
        SELECT user.full_name, timesheet.time_in, timesheet.time_out FROM user LEFT JOIN timesheet ON timesheet.telegram_id = user.telegram_id WHERE date(timesheet.time_in) = (?) OR date(timesheet.time_out) = (?)
    '''
    args = (date,date,date,date)
    results = execute_sql(conn, sql, args).fetchall()
    if(results):
        text = ""
        for index, row in enumerate(results, start=1):
            text = text + str(index) + ". " + row[0] + "\nIn: " + datetime.fromisoformat(row[1]).strftime("%d-%m-%Y %H%M") + "hrs\n" + "Out: " + (datetime.fromisoformat(row[2]).strftime("%d-%m-%Y %H%M") + "hrs \n\n" if isinstance(row[2], str) else "\n\n")
        context.bot.send_message(chat_id=update.callback_query.from_user.id, text=text)

def cancel(update, context):
    update.message.reply_text('Current operation canceled')
    return ConversationHandler.END

if __name__=="__main__":
    sql_create_company_table = """CREATE TABLE IF NOT EXISTS company (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        name text UNIQUE NOT NULL
                                    ); """

    sql_create_user_table = """CREATE TABLE IF NOT EXISTS user (
                                    telegram_id integer PRIMARY KEY,
                                    full_name text UNIQUE NOT NULL,
                                    company_id integer NOT NULL,
                                    FOREIGN KEY (company_id) REFERENCES company (id)
                                );"""

    sql_create_timesheet_table = """CREATE TABLE IF NOT EXISTS timesheet (
                                    id integer PRIMARY KEY AUTOINCREMENT,
                                    telegram_id integer NOT NULL,
                                    time_in text NOT NULL,
                                    time_out text,
                                    FOREIGN KEY (telegram_id) REFERENCES user (telegram_id)
                                );"""

    sql_create_default_company = """INSERT INTO company (name) SELECT 'Bravo' WHERE NOT EXISTS (
                                        SELECT 1 FROM company WHERE name = 'Bravo'
                                    );"""

    #Connect to database
    conn = connect_database(databasePath)

    if conn is not None:
        execute_sql(conn, sql_create_company_table, ())
        execute_sql(conn, sql_create_user_table, ())
        execute_sql(conn, sql_create_timesheet_table, ())
        execute_sql(conn, sql_create_default_company, ())

    #define telegram bot
    updater = Updater(token=botKey, use_context=True)

    #adding handlers to telegram bot
    dispatcher=updater.dispatcher
    dispatcher.add_handler(CommandHandler("setAdmin", setAdmin))
    dispatcher.add_handler(CommandHandler("adminHelp", adminHelp))
    dispatcher.add_handler(CommandHandler("viewHistory", viewUserHistory))
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", help),
            CommandHandler("help", help),
            CommandHandler("create_company", addCompanyMsg),
            CommandHandler("join", saveUserName),
            CommandHandler("getUsers", getUsersMsg),
            CommandHandler("viewInCamp", viewInCampMsg),
            CommandHandler("viewDateHistory", getDate),
            CallbackQueryHandler(bookIn, pattern='^(Book In)$'),
            CallbackQueryHandler(bookOut, pattern='^(Book Out)$'),
        ],
        states={
            SAVE_NAME:[
                MessageHandler(Filters.text & ~Filters.command, saveUserCompany),
            ],
            SAVE_COMPANY:[
                MessageHandler(Filters.text & ~Filters.command, addUser),
            ],
            ADD_COMPANY: [
                MessageHandler(Filters.text & ~Filters.command, addCompany),
            ],
            GET_USERS: [
                MessageHandler(Filters.text & ~Filters.command, getUsers),
            ],
            VIEW_IN_CAMP: [
                MessageHandler(Filters.text & ~Filters.command, viewInCamp),
            ],
            VIEW_DATE_HISTORY: [
                CallbackQueryHandler(viewDateHistory)
            ],
            BIBO: [
                CallbackQueryHandler(bookIn, pattern='^(Book In)$'),
                CallbackQueryHandler(bookOut, pattern='^(Book Out)$'),
            ],
            LOCATION: [
                MessageHandler(Filters.location, authenticateLocation),
                MessageHandler(Filters.regex('^(pass)$'), testbookIn),
            ],
        },
        fallbacks=[CommandHandler('start', help)],
        allow_reentry=True
    )
    dispatcher.add_handler(conv_handler)

    #start telegram bot
    updater.start_polling()
    logger.info("Bot Running")
    #standby mode for telegram bot
    updater.idle()
