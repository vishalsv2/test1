from shared_socketio import socketio , emit , join_room, leave_room , send
from flask import session


@socketio.on('join')
def on_join(data):
    room = data['room']  # Assuming 'room' is the ticket ID here
    join_room(room)
    send('A user has entered the room.', to=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', to=room)