from flask_socketio import SocketIO , emit , join_room, leave_room , send


socketio = SocketIO(cors_allowed_origins="*")
