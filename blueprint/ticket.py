from flask import Blueprint, render_template, redirect, url_for, request, session, Response, send_file, jsonify, flash
from src.Database import Database
from gridfs import GridFS, GridFSBucket
import mimetypes
from blueprint import user
import uuid
from blueprint.api import telegram
from werkzeug.utils import secure_filename
from flask import jsonify
from blueprint.api import telegram
from flask import jsonify
from src.Tickets import Ticket
from datetime import datetime, timedelta

bp = Blueprint("ticket", __name__, url_prefix="/v1/api/tickets")
db = Database.get_connection()

# get all tickets
@bp.route("/", methods=['POST'])
def get_all_tickets():
    """
    Retrieves support tickets from the database and returns them as JSON.

    Returns:
        If the user is authenticated as an admin, the support tickets are retrieved from the database,
        truncated to 250 characters in the 'query' field (if it exists and is a string), and returned as JSON.
        If the user is not authorized, a 403 Forbidden response is returned.

    """
    # check if user sesson and admin
    if session.get('authenticated') and session.get('admin'): 
        tickets = db.ticket.find({})
        truncated_tickets = []
        for ticket in tickets:
            # Ensure 'query' field exists and is of type string before truncating
            if 'query' in ticket and isinstance(ticket['query'], str):
                ticket['query'] = truncate(ticket['query'], 250)
            truncated_tickets.append(ticket)
        # Optionally, convert MongoDB ObjectId to string for JSON serialization or use a custom encoder
        return jsonify(json.loads(dumps(truncated_tickets)))  # Using dumps from bson.json_util for ObjectId compatibility
    else:
        return "You are not authorized to access this resource", 403


@bp.route('/<ticket_id>')
def ticket_details(ticket_id):
    """
    Retrieve ticket details and associated files for a given ticket ID.

    Args:
        ticket_id (str): The ID of the ticket to retrieve details for.

    Returns:
        str: If the ticket is found, it returns the rendered template for ticket details.
             If the ticket is not found, it returns a "Ticket not found" message with a 404 status code.
    """
    ticket = db.ticket.find_one({"ticket_id": ticket_id})
    employees = db.employees.find({})
    username = session.get('name')
    user_document = db.employees.find_one({'name': username})
    if ticket:
        file_docs = list(db.fs.files.find({"metadata.ticket_id": ticket_id}))
        messages = list(db.messages.find({"ticket_id": ticket_id}).sort([("timestamp", 1)])) 
    else:
        return "Ticket not found", 404
    # Fetch associated files from GridFS, if any
    # Assuming you store the filenames or file IDs in the ticket document
    files = []
    if 'file_ids' in ticket:
        for file_id in ticket['file_ids']:
            file_doc = db.fs.files.find_one({'_id': file_id})
            if file_doc:
                files.append(file_doc)

    ticket['files'] = files
    return render_template("ticket_details.html", ticket=ticket, files=file_docs, messages=messages, user_document=user_document, employees=employees)


@bp.route('/assign-tickets', methods=['POST'])
def assign_tickets():
    if request.method == 'POST':
        if not session.get('admin'):
            return jsonify({'error': 'Unauthorized'}), 403

        # Access the JSON data sent in the request
        data = request.get_json() 
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        ticket_ids = data.get('tickets')
        empid = data.get('agent')
        if not ticket_ids or not empid:
            return jsonify({'error': 'Ticket IDs or Employee ID not provided'}), 400

        employee_response = telegram.find_employee(empid)

        if employee_response['status'] != 200:
            return jsonify({'error': 'Employee not found'}), 404 
        try:
            for ticket_id in ticket_ids:
                update_result = telegram.update_ticket_assignment(ticket_id, empid)
                
                if update_result['status'] == 404:
                    return jsonify({'error': f'Ticket ID {ticket_id} not found'}), 404
                    
            return jsonify({'success': 'Tickets successfully assigned', "status": 200})
        except Exception as e:
            return jsonify({'error': 'Failed to assign tickets'}), 500
    else:
        return jsonify({'error': 'Invalid request method'}), 405

@bp.route('/close_ticket/', methods=['POST'])
def handle_close_ticket():
    if request.method == 'POST':
        data = request.get_json() 
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        ticket_id = data.get('ticket_id')
        response = telegram.close_ticket(ticket_id)
        if response['status'] == 200:
            return {'success': response['message'], "status": 200,'redirect_url': url_for('home.dashboard')}
        else:
            return {'error': response['message'], "status": 401}
    else:
        return jsonify({'error': 'Invalid request method'}), 405


@bp.route("/transfer_ticket", methods=['POST'])
def transfer_ticket():
    if request.method == 'POST':
        data = request.get_json() 
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        ticket_id = data.get('ticket_id')
        assigned_to = data.get('assigned_to')
        response = Ticket.transfer_ticket(ticket_id, assigned_to)
        if response['status'] == 200:
            return {
                'success': response['message'],
                'status': 200
            }
        else:
            return {
                'error': response['message'],
                'status': 400
            }
    else:
        return {
            'error': 'Invalid request method',
            'status': 405
        }

@bp.route("/transfer_accept", methods=['POST'])
def transfer_accept():
    if request.method == 'POST':
        data = request.get_json() 
        if not data:
            return {'error': 'No data provided', 'status': 400}
        ticket_id = data.get('ticket_id')
        response = Ticket.transfer_accept(ticket_id)
        if response['status'] == 200:
            return {'success': response['message'], 'status': 200}
        else:
            return {'error': response['message'],
             'status': 400}
    else:
        return {
            'error': 'Invalid request method',
            'status': 405
        }

@bp.route("/transfer_reject", methods=['POST'])
def transfer_reject():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return {'error': 'No data provided', 'status': 400}
        ticket_id = data.get('ticket_id')
        response = Ticket.transfer_reject(ticket_id)
        if response['status'] == 200:
            return {'success': response['message'], 
            'status': 200}
        else:
            return {'error': response['message'], 'status': 400}
    else:
        return {'error': 'Invalid request method', 'status': 405}

def check_ticket_transfers():
    # Define the timeout period (e.g., 48 hours)
    timeout = timedelta(hours=24)
    current_time = datetime.now()

    # Find tickets where the current time exceeds the transfer time + timeout period
    # and the action is still 'pending'
    expired_transfers = tickets.find({
        'action': 'pending',
        'assigned_time': {'$lt': current_time - timeout}
    })

    for ticket in expired_transfers:
        # Revert the ticket to the original assigner or a default handler
        tickets.update_one({'ticket_id': ticket['ticket_id']}, {
            '$set': {
                'assigned_to': ticket['assigned_by'],  # Assuming 'assigned_by' was the original assigner
                'action': 'reverted',
            },
            '$unset': {
                'waiting_for': '',
                'assigned_time': ''
            }
        })
