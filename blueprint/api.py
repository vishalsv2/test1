import uuid
from flask import jsonify, request, session
import requests
from src import generate_ticket_id , get_config
from datetime import datetime   
from datetime import timedelta
from src.Database import Database 
from src.Users import User
import telebot
from shared_socketio import socketio , emit
user_states = {}
db = Database.get_connection()
TOKEN = get_config("bot_token")
bot = telebot.TeleBot(TOKEN, parse_mode=None)
class telegram:
    def create_new_ticket(chat_id, username, issue):
        try:
            ticket_id = generate_ticket_id()
            ticket = {
                "chat_id": chat_id,
                "username": username,
                "status": "open",
                "query": issue,
                "ticket_id": ticket_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "active": 'NULL',
            }
            db.ticket.insert_one(ticket)
            return {"status": 200, "message": "Ticket created successfully", "ticket_id": ticket_id}
        except Exception as e:
            print(f"Error in create_new_ticket: {str(e)}")
            return {"status": 500, "message": "Failed to create a new ticket", "details": str(e)}

    
    def is_user_admin(chat_id, user_id):
        try:
            chat_member = bot.get_chat_member(chat_id, user_id)
            return {"status": 200, "is_admin": chat_member.status in ['administrator', 'creator']}
        except Exception as e:
            print(f"Error in is_user_admin: {str(e)}")
            return {"status": 500, "message": "Failed to check if user is admin", "details": str(e)}

    
    def usernamecheck(message, usernames):
        try:
            if message.from_user.username:
                is_username_in_list = message.from_user.username.lower() in map(str.lower, usernames)
                return {"status": 200, "is_username_valid": is_username_in_list}
            else:
                return {"status": 400, "message": "Username not found in the message"}
        except Exception as e:
            print(f"Error in usernamecheck: {str(e)}")
            return {"status": 500, "message": "Failed to check the username", "details": str(e)}


    def find_employee(empid):
        try:
            # Fetch the employee's data from the MongoDB 'employees' collection
            employee_data = db.employees.find_one({"employee_id": empid})
            
            if employee_data:
                # Employee found, return the name
                return {
                    "status": 200,
                    "message": "Employee found successfully",
                    "name": employee_data.get("username")
                }
            else:
                # Employee not found
                return {
                    "status": 404,
                    "message": "Employee not found"
                }

        except Exception as e:
            # Handle any exceptions that occur during the database operation
            print(f"Error in find_employee: {str(e)}")
            return {
                "status": 500,
                "message": "An error occurred while finding the employee",
                "details": str(e)
            }    
    

    def find_ticket(ticket_id):
        try:
            ticket_document = db.ticket.find_one({"ticket_id": ticket_id})
            if ticket_document:
                return {"status": 200, "ticket": ticket_document}
            else:
                return {"status": 404, "message": "Ticket not found"}
        except Exception as e:
            print(f"Error in find_ticket: {str(e)}")
            return {"status": 500, "message": "Failed to find the ticket", "details": str(e)}

        
    
    def create_session(ticket_id, chat_id, sender_name):
        try:
            session_id = str(uuid.uuid4())
            db.instance.insert_one({
                "ticket_id": ticket_id,
                "session_id": session_id,
                "agent": sender_name,
                "user_id": chat_id,
                "is_active": False,
                "last_interaction": datetime.utcnow()
            })
            return {"status": 200, "message": "Session created successfully", "session_id": session_id}
        except Exception as e:
            print(f"Error in create_session: {str(e)}")
            return {"status": 500, "message": "Failed to create a session", "details": str(e)}



    def store_message(ticket_id, session_id, message_text, sender_name, chat_id,sender_type='user'):
        try:
            db.messages.insert_one({
                "ticket_id": ticket_id,
                "session_id": session_id,
                "text": message_text,
                "sender": sender_name,
                "sender_type": sender_type,
                "user_id": chat_id,
                "last_interaction": datetime.utcnow()
            })
            return {
                "status": 200,
                "message": "Message stored successfully"
            }
        except Exception as e:
            # Log the exception details for debugging, you might use logging module or print statement
            print(f"An error occurred while storing the message: {str(e)}")
            # Return a response indicating the failure
            return {
                "status": 500,
                "message": "Failed to store the message",
                "details": str(e)
            }

    def close_ticket(ticket_id):
        try:
            ticket_document = telegram.find_ticket(ticket_id)
            if ticket_document['status'] == 200:
                # Update the ticket status to closed
                db.ticket.update_one(
                    {"ticket_id": ticket_id},
                    {"$set": {"status": "closed"}}
                )
                return {
                    "status": 200,
                    "message": "Ticket closed successfully"
                }
            else:
                return {
                    "status": 400,
                    "message": "Error: Ticket ID not found"
                }
        except Exception as e:
            print(f"Error in close_ticket: {str(e)}")
            return {"status": 500, "message": "Failed to close the ticket", "details": str(e)}, 500

        
    def process_ticket_issue(message):
        try:
            username = message.from_user.username
            chat_id = message.chat.id
            issue = message.text
            new_ticket_response = telegram.create_new_ticket(chat_id, username, issue)
            if new_ticket_response['status'] == 200:
                ticket_id = new_ticket_response['ticket_id']
                create_user = User.create_ticket_user(username, ticket_id, chat_id)
                if create_user['status']== 200:
                    response_message = (
                        f"Your ticket has been created. Your ticket ID is: *{ticket_id}*\n\n"
                        f"Please upload your screenshots using the command:\n`/uploadfiles {ticket_id}`")
                    bot.reply_to(message, response_message, parse_mode='Markdown')
                    return {"status": 200, "message": "Ticket issue processed successfully"}
                else:
                    print(f"Error {create_user['message']}")
            else:
                return new_ticket_response
        except Exception as e:
            print(f"Error in process_ticket_issue: {str(e)}")
            return {"status": 500, "message": "Failed to process ticket issue", "details": str(e)}


    def verify_session(session_id):
        try:
            session = db.instance.find_one({"session_id": session_id})
            if session:
                return {"status": 200, "session": session}
            else:
                return {"status": 404, "message": "Session not found"}
        except Exception as e:
            print(f"Error in verify_session: {str(e)}")
            return {"status": 500, "message": "An error occurred while verifying the session", "details": str(e)}

    def update_session(session_id, username):
        try:
            update_result = db.instance.update_one(
                {"session_id": session_id},
                {"$set": {
                    "is_active": True,
                    "username": username,
                    "last_interaction": datetime.utcnow()
                }},
                upsert=True
            )
            if update_result.matched_count > 0 or update_result.upserted_id is not None:
                return {"status": 200, "message": "Session updated successfully"}
            else:
                return {"status": 404, "message": "Session not found and upsert was not performed"}
        except Exception as e:
            print(f"Error in update_session: {str(e)}")
            return {"status": 500, "message": "An error occurred while updating the session", "details": str(e)}

    def update_last_interaction(session_id):
        try:
            db.messages.update_one(
                {"session_id": session_id}, 
                {"$set": {"last_interaction": datetime.utcnow()}}
            )
            return {"status": 200, "message": "Last interaction updated successfully"}
        except Exception as e:
            print(f"Error in update_last_interaction: {str(e)}")
            return {"status": 500, "message": "Failed to update last interaction", "details": str(e)}
        
    def update_ticket_assignment(ticket_id, agent_id):
        response = telegram.find_employee(agent_id)
        if response['status'] == 200:
            agent_name = response['name']
        else:
            return {
                "status": 404,
                "message": "Employee not found"
            }
        try:
            # Update the ticket document in the 'ticket' collection
            update_result = db.ticket.update_one(
                {"ticket_id": ticket_id},
                {"$set": {
                    "assigned_by": session['name'],
                    "assigned_to": agent_name,
                    "status": "assigned",
                    "assigned_time": datetime.utcnow()  # Record the time of assignment
                }}
            )

            if update_result.matched_count > 0:
                # The ticket was found and updated
                return {
                    "status": 200,
                    "message": "Ticket assignment updated successfully"
                }
            else:
                # No ticket was found with the given ticket_id
                return {
                    "status": 404,
                    "message": "Ticket not found"
                }

        except Exception as e:
            # Handle any exceptions that occur during the database operation
            print(f"Error in update_ticket_assignment: {str(e)}")
            return {
                "status": 500,
                "message": "An error occurred while updating the ticket assignment",
                "details": str(e)
            }
        # get all the tickets
    def get_all_tickets():
        try:
            tickets = db.ticket.find({})
            return {"status": 200, "tickets": list(tickets)}
        except Exception as e:
            print(f"Error in get_all_tickets: {str(e)}")
            return {"status": 500, "message": "Failed to get all tickets", "details": str(e)}