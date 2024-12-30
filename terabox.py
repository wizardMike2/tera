import os
import re
import requests
import telebot
from time import time
from flask import Flask, jsonify
from threading import Thread
import pymongo
# Define all required variables here
BOT_TOKEN = "6442599880:AAH13m0Xyd6wS6eZsp-Ktbp2GQXsl7WDpPk"
MONGO_URI = "mongodb+srv://deepujallad:Ankityadav7@cluster0.anjrk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
OWNER_ID = "5205248957"  # Use a string if it's not strictly an integer
DUMP_CHAT_ID = "-1002269345174"
CHANNEL_USERNAME = "-1002269345174"

# Initialize bot
bot = Bot(BOT_TOKEN)
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

# Initialize database
client = MongoClient(MONGO_URI)
db = client['DatabaseName']
users_collection = db['users']
banned_users_collection = db['banned_users']

# Flask app for health check
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "Bot is running"})

# Function to verify if user is a channel member
def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# Command: Start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = user.id

    if banned_users_collection.find_one({"user_id": chat_id}):
        update.message.reply_text("You are banned from using this bot.")
        return

    if not is_member(chat_id):
        update.message.reply_text(
            "You must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]
            ])
        )
        return

    if not users_collection.find_one({"user_id": chat_id}):
        users_collection.insert_one({"user_id": chat_id, "downloads": 0})

    update.message.reply_text("Welcome! Send me a Terabox link to start.")

# Command: Ban
def ban(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != OWNER_ID:
        return

    try:
        user_id = int(context.args[0])
        if not banned_users_collection.find_one({"user_id": user_id}):
            banned_users_collection.insert_one({"user_id": user_id})
            update.message.reply_text("User banned successfully.")
        else:
            update.message.reply_text("User is already banned.")
    except Exception:
        update.message.reply_text("Failed to ban user. Provide a valid user ID.")

# Command: Unban
def unban(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != OWNER_ID:
        return

    try:
        user_id = int(context.args[0])
        if banned_users_collection.find_one({"user_id": user_id}):
            banned_users_collection.delete_one({"user_id": user_id})
            update.message.reply_text("User unbanned successfully.")
        else:
            update.message.reply_text("User is not banned.")
    except Exception:
        update.message.reply_text("Failed to unban user. Provide a valid user ID.")

# Command: Broadcast
def broadcast(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != OWNER_ID:
        return

    message = ' '.join(context.args)
    if not message:
        update.message.reply_text("Broadcast message cannot be empty.")
        return

    users = users_collection.find()
    for user in users:
        try:
            bot.send_message(chat_id=user['user_id'], text=message)
        except Exception:
            pass

    update.message.reply_text("Broadcast completed.")

# Video download handler
def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = user.id

    if banned_users_collection.find_one({"user_id": chat_id}):
        update.message.reply_text("You are banned from using this bot.")
        return

    if not is_member(chat_id):
        update.message.reply_text(
            "You must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]
            ])
        )
        return

    url = update.message.text.strip()
    update.message.reply_text("Downloading your video...")

    try:
        # Simulate a download process
        time.sleep(5)  # Replace with actual download logic
        file_name = "video.mp4"

        # Simulate sending the file
        with open(file_name, 'wb') as file:
            file.write(b"Fake video content")

        bot.send_document(chat_id=chat_id, document=open(file_name, 'rb'))
        bot.send_document(chat_id=DUMP_CHAT_ID, document=open(file_name, 'rb'))

        users_collection.update_one({"user_id": chat_id}, {"$inc": {"downloads": 1}})
    except Exception as e:
        update.message.reply_text(f"Failed to download the video: {str(e)}")

# Register handlers
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("ban", ban))
dp.add_handler(CommandHandler("unban", unban))
dp.add_handler(CommandHandler("broadcast", broadcast))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Start Flask app in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=5000)

Thread(target=run_flask).start()

# Start bot polling
updater.start_polling()
updater.idle()
