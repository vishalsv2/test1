from datetime import datetime
from mongogettersetter import MongoGetterSetter
from src.Database import Database
from src.Sessions import Session
from werkzeug.security import  check_password_hash
from flask import session
from datetime import datetime
from mongogettersetter import MongoGetterSetter
from src.Database import Database
from src.Sessions import Session
from werkzeug.security import check_password_hash
from flask import session
import logging
from blueprint.api import telegram
from pymongo.errors import PyMongoError


db = Database.get_connection()
tickets = db.ticket  



class TicketCollection(metaclass=MongoGetterSetter):
    def __init__(self, _id):
        self._collection = tickets
        self._filter_query = {
            '$or': [
                {'ticket_id': _id}
            ]
        }


class Ticket:
    def __init__(self, _id):
        self.collection = TicketCollection(_id)
        self.id = self.collection._id

    @staticmethod
    def transfer_ticket(ticket_id, assigned_to):
        # Check if the ticket is being transferred to the same user trying to make the transfer
        if assigned_to == session.get('name'):
            return {'status': 400, 'message': 'Error: Cannot transfer ticket to yourself.'}

        response = telegram.find_employee(assigned_to)
        if response['status'] == 404:
            # Error: Employee not found
            return {'status': 404, 'message': 'Error: Employee not found.'}

        agent_name = response['name']

        # Check if the ticket is already assigned to the requested user with action 'pending'
        existing_ticket = tickets.find_one({'ticket_id': ticket_id})
        
        # This print might raise an error if existing_ticket is None
        # Consider adding a check if existing_ticket is not None before accessing its properties
        if existing_ticket:

            if existing_ticket['action'] == 'pending':
                return {'status': 409, 'message': "Error: Ticket cannot be transferred again until it's rejected."}
            else:
                # Proceed with transferring the ticket
                new_transfer_count = existing_ticket.get('transfer_count', 0) + 1
                tickets.update_one({'ticket_id': ticket_id}, {
                    '$set': {
                        'waiting_for': agent_name,
                        'assigned_by': session.get('name'),
                        'assigned_time': datetime.now(),
                        'action': 'pending',
                        'transfer_count': new_transfer_count  # Keep track of transfer attempts to the same user
                    }
                })
                # Success: Ticket transferred successfully
                return {'status': 200, 'message': 'Ticket transferred successfully.'}
        else:
            # Error: Ticket not found
            return {'status': 400, 'message': 'Error: Ticket not found.'}

    @staticmethod
    def transfer_accept(ticket_id):
        ticket = tickets.find_one({'ticket_id': ticket_id, 'waiting_for': session.get('name'), 'action': 'pending'})
        if ticket:
            tickets.update_one({'ticket_id': ticket_id}, {
                '$set': {'action': 'accepted', 'assigned_to': session.get('name')},
                '$unset': {'waiting_for': ''}
            }, upsert=False)
            return {'status': 200, 'message': 'Ticket accepted successfully'}
        else:
            return {'status': 400, 'message': 'Error: Ticket not found.'}

    @staticmethod
    def transfer_reject(ticket_id):
        ticket = tickets.find_one({'ticket_id': ticket_id, 'waiting_for': session.get('name'), 'action': 'pending'})
        if ticket:
            tickets.update_one({'ticket_id': ticket_id}, {
                '$set': {'action': 'rejected', 'waiting_for': ''}
            })
            return {'status': 200, 'message': 'Ticket rejected successfully'}
        else:
            return {'status': 400, 'message': 'Ticket not found'}