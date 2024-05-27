from flask import Blueprint, request, jsonify
from blueprint.api import telegram
from src import get_config
from datetime import datetime
from src.Database import Database
from src.Users import User
from flask import Blueprint, render_template, redirect, url_for, request, session, Response, send_file,jsonify
from src import get_config 
from src.Database import Database
from bson.objectid import ObjectId
import requests
from datetime import timedelta
import uuid
import telebot
from telebot import types
import os
import sys
from shared_socketio import socketio , emit , send
from datetime import datetime

# Initialize the Telegram bot
db = Database.get_connection()
TICKET_VALIDITY_DURATION_MINUTES = get_config("TICKET_VALIDITY_DURATION")
TICKET_VALIDITY_DURATION = timedelta(minutes=TICKET_VALIDITY_DURATION_MINUTES)
TOKEN = get_config("bot_token")
admin_user = get_config("admin")
bot = telebot.TeleBot(TOKEN, parse_mode=None)
user_states = {}
webhook = get_config("web_hool_url")
url = get_config("url")

bp = Blueprint("telegram", __name__, url_prefix="/v1/api/telegram")


# Don't touch this below routes.
@bp.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook('{}/{}'.format(webhook, TOKEN))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"



@bp.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    update = telebot.types.Update.de_json(request.get_json(force=True))
    bot.process_new_updates([update])

    return 'ok'
  # Return an error message with HTTP status code 500 (Internal Server Error)

# Don't touch this above routes.    



# Telegram code starts from here 

@bot.message_handler(commands=['newticket'])
def new_ticket(message):
    try:
        msg = bot.reply_to(message, "Please describe your issue:")
        bot.register_next_step_handler(msg, telegram.process_ticket_issue)
    except Exception as e:
        print(f"Error in new_ticket: {str(e)}")
        bot.send_message(message.chat.id, "Oops! Something went wrong. Please try again.")


@bot.message_handler(commands=['uploadfiles'])
def prompt_file_upload(message):
    try:
        args = message.text.split()  # Split command and arguments
        user_id = message.from_user.id

        # Fetch the user's state from the MongoDB 'users' collection
        user_data = db.users.find_one({"chat_id": user_id})

        if not user_data or 'state' not in user_data:
            bot.reply_to(message, "Please create a ticket first using /newticket.")
            return

        ticket_creation_time = user_data.get('creation_time')
        current_time = datetime.now()
        if not ticket_creation_time or current_time - ticket_creation_time > TICKET_VALIDITY_DURATION:
            bot.reply_to(message, "Your ticket has expired. Please create a new ticket.")
            return

        # Check if user is in 'awaiting_file_upload' state and has created a ticket
        if user_data.get('state') != 'awaiting_file_upload':
            bot.reply_to(message, "Please create a ticket first using /newticket.")
            return

        # Check if the user has provided a ticket ID
        if len(args) < 2:
            bot.reply_to(message, "Please provide a ticket ID. Usage: /uploadfiles <ticket_id>")
            return

        provided_ticket_id = args[1]
        expected_ticket_id = user_data.get('ticket_id')

        # Validate the provided ticket ID
        if provided_ticket_id != expected_ticket_id:
            bot.reply_to(message, "Invalid ticket ID. Please use the ticket ID provided after creating your ticket.")
            return

        # Prompt the user to send the file
        bot.reply_to(message, "Please upload your file now.")
        
        # Update the user's state to 'uploading_file' in the MongoDB 'users' collection
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"state": 'uploading_file'}}
        )
    except Exception as e:
        print(f"Error in prompt_file_upload: {str(e)}")
        bot.send_message(message.chat.id, "Oops! Something went wrong. Please try again.")


@bot.message_handler(content_types=['document', 'photo'])
def handle_docs(message):
    try:
        user_id = message.from_user.id
        # Fetch the user's data from the MongoDB 'users' collection
        user_data = db.users.find_one({"chat_id": user_id})
        

        if not user_data or user_data.get('state') != 'awaiting_file_upload':
            bot.reply_to(message, "You need to use /uploadfiles <ticket_id> to start the file upload process.")
            return
        
        file_size = None  # Initialize file_size to None

        if message.content_type == 'document':
            document = message.document
            file_id = document.file_id
            file_size = document.file_size
            allowed_file_types = ['application/pdf', 'image/jpeg', 'image/png']  # Add or remove allowed types as needed
            if document.mime_type not in allowed_file_types:
                bot.reply_to(message, "Unsupported file type. Please upload a PDF, JPEG, or PNG.")
                return
        elif message.content_type == 'photo':
            photo = message.photo[-1]
            file_id = photo.file_id
            # File size is not directly available for photos, consider checking resolution or document a size assumption
        else:
            bot.reply_to(message, "Unsupported content type.")
            return

        # Check file size (Telegram servers limit file sizes to 20MB for bots, adjust as needed)
        if file_size and file_size > 10 * 1024 * 1024:  # 10 MB
            bot.reply_to(message, "The file size is too large. Please upload a file smaller than 10MB.")
            return

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Retrieve the ticket_id from the user's data
        ticket_id = user_data['ticket_id']

        # Prepare the file to send to Flask
        files = {'file': (file_info.file_path, downloaded_file)}
        data = {'ticket_id': ticket_id}
        response = requests.post(f'{url}/v1/api/files/upload', files=files, data=data)

        if response.status_code == 200:
            bot.reply_to(message, "File uploaded successfully.")
            # Consider updating the user state in the database to reflect the change
            new_user_state = {
                'state': 'file_uploaded',  # Set to the next state in your workflow
                'last_interaction': datetime.now()  # Update the last interaction time
            }
            db.users.update_one(
                {"chat_id": user_id},
                {"$set": new_user_state}
            )
            print(f"User state updated: {new_user_state}")
        else:
            bot.reply_to(message, f"Failed to upload file. Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"Error in handle_docs: {str(e)}")
        bot.send_message(message.chat.id, "Oops! Something went wrong. Please try again.")
    

@bot.message_handler(commands=['restart'])
def restart_bot(message):
    if telegram.usernamecheck(message,admin_user) and message.chat.type in ["private"]:
        bot.reply_to(message, "Restarting...")
        print(message.from_user.username)
        os.execl(sys.executable,sys.executable,*sys.argv)
    else:
        bot.delete_message(message.chat.id,message.message_id)


@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        sender = message.from_user.id
        username = message.from_user.username
        command_args = message.text.split()
        if len(command_args) <= 1:
            bot.reply_to(message, "Please provide a session ID. Usage: /start <session_id>")
            return

        session_id = command_args[1]

        # Fetch the session using the telegram class method
        session_response = telegram.verify_session(session_id)

        if session_response['status'] == 200:
            # Session exists, update its status using the telegram class method
            update_response = telegram.update_session(session_id, username)
            if update_response['status'] == 200:
                bot.reply_to(message, "Session started with session ID: " + session_id)
            else:
                # Handle update failure
                bot.reply_to(message, update_response['message'])
        else:
            # Handle session verification failure
            bot.reply_to(message, session_response['message'])

    except Exception as e:
        print(f"Error in handle_start: {str(e)}")
        bot.reply_to(message, "An error occurred. Please try again.")


@bot.message_handler(func=lambda message: True)
def store_message(message):
    try:
        if message.text.startswith('/'):
            return

        message_text = message.text
        username = message.from_user.username
        sender = message.from_user.id

        # Fetch the active session for this sender using the telegram class method
        active_session_response = telegram.find_active_session_by_user(sender)

        if active_session_response['status'] == 200:
            session = active_session_response['session']
            session_id = session["session_id"]
            ticket_id = session["ticket_id"]

            # Store the message using the telegram class method
            store_result = telegram.store_message(ticket_id, session_id, message_text, username, sender, sender_type='user')

            if store_result['status'] == 200:
                print(f"About to emit message to room {ticket_id}: {message_text}")
                last_interaction = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                socketio.emit('message_from_telegram', {
                    'ticket_id': ticket_id,
                    'message': message_text,
                    'sender': sender,
                    'last_interaction': last_interaction
                })
                print(f"Emitted message: {message_text}")
                bot.reply_to(message, 'Message Sent')

                # Update the last interaction timestamp using the telegram class method
                update_interaction_response = telegram.update_last_interaction(session_id)
                if update_interaction_response['status'] != 200:
                    print(f"Failed to update last interaction: {update_interaction_response['message']}")
            else:
                # Handle store message failure
                bot.reply_to(message, store_result['message'])
                print(f"Failed to store message: {store_result['message']}")
        else:
            # No active session found for this user
            bot.reply_to(message, 'No active session found. Please start a new session.')
    except Exception as e:
        print(f"Error in handle_start: {str(e)}")
        bot.reply_to(message, "An error occurred. Please try again.")


# Telegram bot code ends here ....
        
# Socket code starts from here .....
        
@socketio.on('send_message')
def send_message(data):
        try:
            ticket_id = data['ticket_id']
            ticket_document = telegram.find_ticket(ticket_id)
            print(ticket_id)
            print("Inside the loop")
            if ticket_document:
                chat_id = ticket_document.get("chat_id")
                message_text = data['message']
                sender_name = session['name']
                sender_type = session['type']
                # Check if there's an active session in the messages collection for this ticket_id
                active_session = telegram.find_active_session(ticket_id)

                if active_session:
                    # Active session found, use its session_id
                    session_id = active_session.get("session_id")
                else:
                    # No active session, create a new one
                    session_id = telegram.create_session(ticket_id, chat_id, sender_name)
                    # Construct the deep link
                    deep_link = f"https://t.me/Selfmade_ninja_Academy_bot?start={session_id}"
                    message_text = f"{message_text} Please click the link to start your support session: {deep_link}"
                # Prepare the request to the Telegram API to send the message
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                params = {
                    "chat_id": chat_id,
                    "text": message_text,
                }
                # Send the message via the Telegram API 
                response = requests.post(url, params=params)
                print(response)

                # If the message was sent successfully, store the message
                if response.status_code == 200:
                    # Store or update the message in the 'messages' collection
                    response = telegram.store_message(ticket_id, session_id, message_text, sender_name, chat_id,sender_type)
                    if response['status'] == 200:
                        last_interaction = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        print('Emitting data:', message_text)
                        send('message_response', {
                            'ticket_id': ticket_id,
                            'message': message_text,    
                            'sender': sender_name,
                            'last_interaction': last_interaction
                        }, to=ticket_id)
                        print('Emitted data:', message_text)
                        return jsonify({'status': 'success', 'message': 'Message sent successfully', 'data': {'ticket_id': ticket_id}}),200
                    else:
                        return jsonify({'status': 'error', 'message': 'Failed to store the message in the Mongodb'}),404
                else:
                    return jsonify({'status': 'error', 'message': 'Failed to send message via Telegram API'}), 500
            else:
                return jsonify({'status': 'error', 'message': 'Ticket not found'}), 404
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'An error occurred', 'details': str(e)}), 500
        

# Socket code ends here....