from datetime import datetime  
from mongogettersetter import MongoGetterSetter
from src.Database import Database
from src.Sessions import Session
from werkzeug.security import  check_password_hash

db = Database.get_connection()
users = db.users  # This collection will store both agents and Telegram users

class UserCollection(metaclass=MongoGetterSetter):
    def __init__(self, username):
        self._collection = db.users
        self._filter_query = {
            "$or": [
                {"username": username}, 
                {"id": username}
            ]
        }

class User:
    def __init__(self, id):
        self.collection = UserCollection(id)
        self.id = self.collection.id
        self.username = self.collection.username        

    @staticmethod
    def create_agent(username, password, position, department, employee_id):
        try:
            # Check if the agent already exists in the user collection
            existing_agent = db.employees.find_one({"username": username})
            if existing_agent:
                raise Exception("Agent with this username already exists")

            # Determine role based on the position
            role = 'Admin' if position.lower() == 'admin' else 'Agent'

            employee_document = {
                "username": username,
                "position": position,
                "department": department,
                "employee_id": employee_id,
                "password": password,
                "active": False,
                "avatar": None,
                "role": role  # Set role based on the position
            }

            db.employees.insert_one(employee_document)
            
            return {
                "status": 200,
                "message": f"{role} Successfully Registered"
            }

        except Exception as e:
            return {
                "status": 400,  # You can choose an appropriate HTTP status code for the error
                "message": str(e)  # Return the error message as the response
            }


    @staticmethod
    def create_ticket_user(username, ticket_id, chat_id):
        try:
            # Prepare the user state data
            user_state_data = {
                'state': 'awaiting_file_upload',
                'ticket_id': ticket_id,
                'creation_time': datetime.now()
            }

            # Check if the Telegram user already exists in the user collection
            existing_user = db.users.find_one({"username": username})

            if not existing_user:
                # If the user doesn't exist, create a new entry with user state data
                db.users.insert_one({
                    "username": username,
                    "role": "Telegram User",
                    "tickets": [ticket_id],
                    "chat_id": chat_id,
                    **user_state_data  # Merge user_state_data into the document
                })
            else:
                # If the user already exists, update their tickets array and user state data
                db.users.update_one(
                    {"username": username},
                    {
                        "$push": {"tickets": ticket_id},
                        "$set": user_state_data  # Update user state data
                    }
                )

            return {
                "status": 200,
                "message": "Telegram User Successfully Registered",
            }

        except Exception as e:
            return {
                "status": 400,  # You can choose an appropriate HTTP status code for the error
                "message": str(e),  # Return the error message as the response
            }

    @staticmethod
    def agent_login(username, password):
        try:
            user = db.employees.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                query = {"username": username}
                new_values = {"$set": {"active": True}}
                db.employees.update_one(query, new_values)
                session = Session.register_session(username)
                position = user['position']
                username = user['username']
                empid = user['employee_id']
                type = user['role']
                return {
                    "status": 200,
                    "message": "Agent Successfully Logged In",
                    "session_id": session,
                    "position": position,
                    "username": username,
                    "employee_id": empid,
                    "type": type
                }
            else:
                # Agent login failed
                raise Exception("Invalid credentials")

        except Exception as e:
            return {
                "status": 400,  # You can choose an appropriate HTTP status code for the error
                "message": str(e)  # Return the error message as the response
            }
        
    def is_admin(self):
        return self.collection.position == 'admin'