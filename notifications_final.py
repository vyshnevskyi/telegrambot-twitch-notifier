# -*- coding: utf-8 -*-
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import os.path
from pymongo import MongoClient
from time import gmtime, strftime
import requests
import json
import sys
import logging
import pprint
from time import sleep

updater = Updater(token='TELEGRAM_API_KEY')
dispatcher = updater.dispatcher
job = updater.job_queue
#DB connect#

client = MongoClient('localhost', 27017)
db = client['notify']
users = db['users']


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)



# /start function #

def start (bot, update):
	bot.send_message(chat_id=update.message.chat_id, text="Hi, i'm able to different cool stuff, use /list to see more")
	ids = update.message.chat_id
	i=0
	if db.users.find_one({"ID": ids}) is None:
		usid = [{"ID": ids, "Twitch": [""]}]
		result = users.insert_many(usid).inserted_ids
		log = "\n" + "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "]" + " UserID " + str(ids) + " just started to use this bot"
		log_file = open('bot.log','a')
		log_file.write(log)
		log_file.close()

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)




# /list commandlist function #

def list (bot, update):
	bot.send_message(chat_id=update.message.chat_id, text = "/sub to sub to twitch channel \n/unsub to unsub from twitch channel \n/sublist to view your subscriptions")

list_handler = CommandHandler ('list', list)
dispatcher.add_handler(list_handler) 

#def twitch_sub (bot,update):

	
def twitch_sub(bot,update,args):
        channel_name = ''.join(args).lower()
        ids = update.message.chat_id
        suber = db.users.find_one({"ID": ids})
        sublist = suber["Twitch"]
	headers = {'Client-ID': 'TWITCH_API_KEY'}
	flow_data = requests.get("https://api.twitch.tv/kraken/channels/%s" % channel_name, headers=headers)
	flow_info = json.loads(flow_data.text)
	try:
		if flow_info['name'] is None:
			bot.send_message(chat_id=ids, text = "Sorry, this channel doesn't exit")
			return
	except:
		bot.send_message(chat_id=ids, text = "Sorry, this channel doesn't exit")
		log = "\n" + "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "]" + " UserID: " + str(ids) + " tried to subscribe to " + channel_name + " which doesnt exist"
		log_file = open('bot.log','a')
		log_file.write(log)
		log_file.close()
		return
        i=0
        j=0
        while i < len(sublist):
        	if suber["Twitch"][i] == channel_name:
        		j+=1
        	i+=1
        if j>0:
        	bot.send_message(chat_id=ids, text ="You're already subsribed to  "+channel_name)
        	log = "\n" + "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "]" + " UserID: " + str(ids) + " just tried to subscribe to " + channel_name + " though he is already subscibed"
        	log_file = open('bot.log','a')
		log_file.write(log)
		log_file.close()
        else:	
        	db.users.update_one({"ID": ids}, {"$push": {"Twitch": channel_name}})
		bot.send_message(chat_id=ids, text = "Succesfully subscribed to "+channel_name)
		log = "\n" + "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "]" + " UserID: " + str(ids) + " just subscribed to " + channel_name
		log_file = open('bot.log','a')
		log_file.write(log)
		log_file.close()
	if db.streamers.find_one({"stream_name": channel_name}) is None:
		flower = [{"stream_name": channel_name, "flag": 0}]
		db.streamers.insert_many(flower)
		log = "\n" + "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "] " + channel_name + " was just added to Streamers DB"
		log_file = open('bot.log','a')
		log_file.write(log)
		log_file.close()
	

twitchsub_handler = CommandHandler('sub', twitch_sub,pass_args=True)
dispatcher.add_handler(twitchsub_handler)

#def /sublist

def sublist(bot,update):
	ids = update.message.chat_id
	subs = db.users.find_one({"ID": ids})
	twitch_subs = []
	j = 0
	while j < len(subs['Twitch']):
		sub = subs['Twitch'][j]
		twitch_subs.append([sub])
		j+=1

	if twitch_subs == []:
		bot.send_message(chat_id=ids, text = "To subscribe /sub channel_name")
	else:
		bot.send_message(chat_id=ids, text = "You're subscribed to " + str(subs["Twitch"]).replace("[","").replace("]","").replace("u'","").replace("'",""))


sublist_handler = CommandHandler('sublist', sublist)
dispatcher.add_handler(sublist_handler)

def unsub(bot,update,args):
	channel_name = ''.join(args).lower()
	ids = update.message.chat_id
	user = db.users.find_one({"ID": ids})
	sublist = user["Twitch"]
	db.users.update_one({"ID": ids}, {"$pull": {"Twitch": channel_name} } )
	bot.send_message(chat_id=ids, text = "You're no more subscribed to " + channel_name)
	log = "\n" + "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "] " + "UserID: " + str(ids) + " just unsubscribed from " + channel_name
	log_file = open('bot.log','a')
	log_file.write(log)
	log_file.close()

unsub_handler = CommandHandler('unsub', unsub, pass_args=True)
dispatcher.add_handler(unsub_handler)

# Not a command command echo #

def echo (bot, update):
	bot.send_message(chat_id=update.message.chat_id, text="This is not a command, mate")

echo_handler = MessageHandler (Filters.text, echo)
dispatcher.add_handler(echo_handler)

# Unknown command echo #

def unknown (bot, update):
	bot.send_message(chat_id=update.message.chat_id , text = "We still didn't invent such a command, please contact Elon Musk")


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

# Job Queue Function #


def callback_func(bot,job):
	headers = {'Client-ID': 'Twitch_API_KEY'}
	calls = 0
	for streamlist in db.streamers.find():
		stream_name = streamlist['stream_name']
		flags = streamlist['flag']
		sleep(1)
		if (db.users.find_one({"Twitch": stream_name}) is not None):
			flow_data = requests.get("https://api.twitch.tv/kraken/streams/%s" % stream_name, headers=headers)
			calls+=1
			flow_info = json.loads(flow_data.text)
			if flow_info['stream'] is not None:
				if flags == 0:
					log = "\n" +  "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "] "+ stream_name + " is live now!"
					log_file = open('bot.log','a')
					log_file.write(log)
					log_file.close()
					flow_game=flow_info['stream']['channel']['game']
					for clients in db.users.find({"Twitch": stream_name}):
						chat_ids = clients["ID"]
						bot.send_message(chat_id=chat_ids, text = "Hello, "+ stream_name + " is live now! \n He's playing " + flow_game + "\n Link: https://twitch.tv/"+stream_name)
					db.streamers.update_one({"stream_name":stream_name},{"$set": {"flag": 1}})
			else:
				db.streamers.update_one({"stream_name":stream_name},{"$set": {"flag": 0}})
	print "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "] This time i did " + str(calls) + " requests to Twitch API"
	log = "\n" + "[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "] This time i did " + str(calls) + " requests to Twitch API"
	log_file = open('bot.log','a')
	log_file.write(log)
	log_file.close()
			
		
job_minute = job.run_repeating(callback_func, interval=120, first=0)


updater.start_polling()
updater.idle()
