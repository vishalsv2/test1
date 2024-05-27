from flask import Blueprint, render_template, redirect, url_for, request, session,jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

from src.Database import Database
from src import truncate, generate_employee_id
from src.Users import User

bp = Blueprint("user", __name__, url_prefix="/v1/api/users")
db = Database.get_connection()



@bp.route('/get_documents', methods=['GET'])
def get_documents():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Missing username'}), 400
    
    documents = db.ticket.find({'assigned_to': username})
    
    # Convert documents to a list (as find() returns a cursor)
    result = list(documents)
    
    # Convert the ObjectId to string because it's not JSON serializable
    for document in result:
        document['_id'] = str(document['_id'])
    
    return jsonify(result), 200



@bp.route("/profile")
def profiles():
    username = session.get('name')
    user_document = db.employees.find_one({'name': username})
    return render_template("_profile.html",session=session,user_document=user_document)


@bp.route("/emplist")
def employee():
    username = session.get('name')
    user_document = db.employees.find_one({'username': username})
    employees = db.employees.find({})
    return render_template("_emplist.html",employees=employees,user_document=user_document)
 

@bp.route("/register",methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('name')
        position = request.form.get('position')
        department = request.form.get('department')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        employee_id = generate_employee_id()
        response = User.create_agent(username,hashed_password,position,department,employee_id)
        if response["status"] == 200:
            return redirect(url_for('user.employee'))
        else:
            return jsonify({'error': response["message"] }), 400

        
@bp.route("/pending")
def pending():
    username = session.get('name')
    user_document = db.employees.find_one({'name': username})
    tickets = db.ticket.find({'waiting_for': username})
    tickets = list(tickets)
    if tickets is None:
        tickets = []
    print(tickets)
    return render_template("_pending.html",session=session, user_document=user_document, tickets=tickets)

@bp.route("/logout", methods=['POST', 'GET'])
def logout():
    session.clear()  # This will clear all the session variables
    return render_template('login.html')


@bp.route("/login",methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    respoce = User.agent_login(username, password)
    if respoce['status'] == 200:
        if respoce['position']=="admin":
            session['authenticated']=True
            session['name']=respoce['username']
            session['role']=respoce['position']
            session['employee_id']=respoce['employee_id']
            session['admin']=True
            flash('You were successfully logged in', category='error')
            return redirect(url_for('home.dashboard'))
        else:
            session['authenticated']=True
            session['name']=respoce['username']
            session['role']=respoce['position'] 
            session['employee']=True
            session['employee_id']=respoce['employee_id']
            session['type']=respoce['type']
            return redirect(url_for('home.dashboard'))    
    else:
        return jsonify({'message': 'Invalid username or password'}), 401


@bp.route("/is_active", methods=['GET'])
def is_active():
    username = session.get('name')
    if not username:
        return jsonify({'error': 'User not logged in or session expired'}), 401


    user_document = db.employees.find_one({"name": username})

    if not user_document:
        return jsonify({'error': 'User not found'}), 404

    is_active = user_document.get('active', False)

    return jsonify({'active': is_active}), 200


@bp.route("/activated", methods=['POST'])
def iamalive():
    username = session.get('name')
    if not username:
        return jsonify({'error': 'User not logged in or session expired'}), 401

    query = {"name": username}
    new_values = {"$set": {"active": True}}
    
    db.employees.update_one(query, new_values)
    return jsonify({'message': f'User {username} activated successfully!'}), 200

@bp.route("/deactivated", methods=['POST'])
def iamnotalive():
    username = session.get('name')
    if not username:
        return jsonify({'error': 'User not logged in or session expired'}), 401

    query = {"name": username}
    new_values = {"$set": {"active": False}}
    
    db.employees.update_one(query, new_values)

    # Return a valid response
    return jsonify({'message': f'User {username} deactivated successfully!'}), 200
  