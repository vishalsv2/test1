from flask import Blueprint, render_template, redirect, url_for, request, session,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from math import ceil
from bson.json_util import dumps
import json
from src.Database import Database
from src import truncate, generate_employee_id
from src.Tickets import Ticket

bp = Blueprint("home", __name__, url_prefix="/")
db = Database.get_connection()
collection = db.ticket
collection2=db.employees


@bp.route("/")
def home():
    """
    Renders the login.html template with the session object.

    Returns:
        The rendered login.html template.
    """
    return render_template("login.html", session=session)


@bp.route("/dashboard")
@bp.route("/dashboard/<int:page>")
def dashboard(page=1):
    """
    Renders the dashboard page with support tickets and user information.

    Args:
        page (int, optional): The page number for pagination. Defaults to 1.

    Returns:
        The rendered template for the dashboard page.
    """
    if session.get('authenticated'):
        per_page = 10
        tickets = collection.find({})
        employees = db.employees.find({})
        total_tickets = collection.count_documents({})
        total_pages = ceil(total_tickets / per_page)
        tickets = collection.find({}).skip((page - 1) * per_page).limit(per_page)
        truncated_tickets = []
        for ticket in tickets:
            # Ensure 'query' field exists and is of type string before truncating
            if 'query' in ticket and isinstance(ticket['query'], str):
                ticket['query'] = truncate(ticket['query'], 300)
            truncated_tickets.append(ticket)

        username = session.get('name')
        mydata = []  

        if session.get('admin'):
            mydata = []  # or set it to whatever nodata is supposed to represent
        else:
            documents = collection.find({'assigned_to': username})
            mydata = list(documents)
            for document in mydata:
                document['_id'] = str(document['_id'])

        
        user_document = collection2.find_one({'name': username})

        # user_document = collection2.find_one({'name': username})

        return render_template("dashboard.html",user_document=user_document,mydata=mydata, tickets=truncated_tickets,current_page=page,total_pages=total_pages,session=session,employees=employees)
    else:
        return render_template("login.html")


    
# employee assigned tickets
# @bp.route("/employee_tickets", methods=['POST'])
# def employee_tickets():
#     """
#     Retrieves the tickets associated with the logged-in employee.

#     Returns:
#         If the user is not logged in or the session is invalid, returns a JSON response with an error message and a status code of 401.
#         If there are no tickets available for the user, returns a JSON response with a message and a status code of 404.
#         If an unexpected error occurs, returns a JSON response with an error message and a status code of 500.
#         If the tickets are successfully retrieved, returns a JSON response with the tickets and a status code of 200.
#     """
#     user_name = session.get('name')
#     if not user_name:
#         return jsonify({'error': 'User is not logged in or session is invalid.'}), 401

#     try:
#         tickets = Ticket.employee_tickets(user_name)
#         if tickets['status'] == 404:
#             return jsonify({'message': 'No tickets available for this user.'}), 404
#         elif tickets['status'] == 500:
#             return jsonify({'error': 'An unexpected error occurred.'}), 500
#         return jsonify(json.loads(dumps(tickets)))
#     except Exception as e:
#         print(f"Unexpected error: {e}")
#         return jsonify({'error': 'An unexpected error occurred.'}), 500



# write code for transfer ticket
# @bp.route("/transfer_ticket", methods=['POST'])
# def transfer_ticket():
#     try:
#         ticket_id = request.form.get('ticket_id')
#         assigned_to = request.form.get('assigned_to')
        
#         # Check if the user is logged in and has a name in the session
#         user_name = session.get('name')
#         if not user_name:
#             return jsonify({'error': 'User is not logged in or session is invalid.'}), 401
        
#         # Assuming Ticket initialization and method calls work as expected
#         ticket = Ticket(user_name)
#         response = ticket.transfer_ticket(ticket_id, assigned_to)
#         return jsonify(response)
#     except Exception as e:
#         # Log the error here (e.g., app.logger.error(e))
#         print(f"Unexpected error: {e}")
#         return jsonify({'error': 'An unexpected error occurred.'}), 500
    

# @bp.route("/transfer_accept", methods=['POST'])
# def transfer_accept():
#     try:
#         ticket_id = request.form.get('ticket_id')
#         assigned_to = request.form.get('assigned_to')
        
#         # Check if the user is logged in and has a name in the session
#         user_name = session.get('name')
#         if not user_name:
#             return jsonify({'error': 'User is not logged in or session is invalid.'}), 401
        
#         # Assuming Ticket initialization and method calls work as expected
#         ticket = Ticket(user_name)
#         response = ticket.transfer_accept(ticket_id, assigned_to)
#         return jsonify(response)
#     except Exception as e:
#         # Log the error here (e.g., app.logger.error(e))
#         return jsonify({'error': 'An unexpected error occurred.'}), 500


# @bp.route("/support_tickets")
# def support_tickets():
#     """
#     Render the support tickets page with truncated support tickets.

#     Retrieves all support tickets from the collection and truncates the 'query' field
#     to a maximum of 250 characters if it exists and is of type string. The truncated
#     tickets are then passed to the 'support_tickets.html' template for rendering.

#     Returns:
#         The rendered 'support_tickets.html' template with the truncated support tickets.
#     """
#     tickets = collection.find({})
#     truncated_tickets = []
#     for ticket in tickets:
#         # Ensure 'query' field exists and is of type string before truncating
#         if 'query' in ticket and isinstance(ticket['query'], str):
#             ticket['query'] = truncate(ticket['query'], 250)
#         truncated_tickets.append(ticket)
#     return render_template("support_tickets.html", tickets=truncated_tickets)




