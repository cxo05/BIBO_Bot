import sqlite3
from sqlite3 import Error
from telegram.ext import Updater as up
from telegram.ext import CommandHandler as ch
from telegram.ext import MessageHandler,Filters
from telegram import File
import logging
from math import sin, cos, sqrt, atan2, radians
from datetime import datetime

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
    
def createtable():
    conn = sqlite3.connect("C:\\sqlite3 database\sm_app.sqlite")
    c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS BIBO (name text,date text,time text)')
    print("table created")
    conn.commit()
    conn.close()

def checkin(update,context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Pls type your rank and name")
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, addname))
    
def addname(update,context):    
    n1=update.message.text
    conn = sqlite3.connect("C:\\sqlite3 database\sm_app.sqlite")
    c=conn.cursor()
    now = datetime.now()
    date= now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")
    c.execute('INSERT INTO BIBO (NAME,DATE,TIME) VALUES (?,?,?)', [n1,date,time])
    conn.commit()
    conn.close
    context.bot.send_message(chat_id=update.effective_chat.id, text=n1+" is added")

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
    
    #creates sqlite table
    createtable()

    #define telegram bot
    updater = up(token='1763270773:AAFKJWzDPLSi03-pjRBD4aaT_X9co4hSlw8', use_context=True)

    #logging errors above warning
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
    
    #adding handlers to telegram bot
    dispatcher=updater.dispatcher
    dispatcher.add_handler(ch("start", start))
    dispatcher.add_handler(ch("add",authenticate))
    
    #start telegram bot
    updater.start_polling()
    print("bot running")
    #standby mode for telegram bot
    updater.idle()

   













