from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_123'
socketio = SocketIO(app)

# Очередь для мэтчинга
waiting_users = {}
active_pairs = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Новый пользователь подключился:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in active_pairs:
        partner_id = active_pairs[user_id]
        emit('partner_disconnected', room=partner_id)
        del active_pairs[partner_id]
    if user_id in waiting_users:
        del waiting_users[user_id]

@socketio.on('join_queue')
def handle_join_queue(data):
    user_id = request.sid
    waiting_users[user_id] = {
        'username': data['username'],
        'bio': data['bio']
    }
    
    # Если есть кто-то в очереди — соединяем
    if len(waiting_users) >= 2:
        users = list(waiting_users.items())
        user1_id, user1_data = users[0]
        user2_id, user2_data = users[1]
        
        # Создаем пару
        active_pairs[user1_id] = user2_id
        active_pairs[user2_id] = user1_id
        
        # Удаляем из очереди
        del waiting_users[user1_id]
        del waiting_users[user2_id]
        
        # Отправляем данные друг другу
        emit('chat_start', {
            'partner_username': user2_data['username'],
            'partner_bio': user2_data['bio']
        }, room=user1_id)
        
        emit('chat_start', {
            'partner_username': user1_data['username'],
            'partner_bio': user1_data['bio']
        }, room=user2_id)

@socketio.on('send_message')
def handle_message(data):
    user_id = request.sid
    if user_id in active_pairs:
        partner_id = active_pairs[user_id]
        emit('new_message', {
            'text': data['text'],
            'time': data['time']
        }, room=partner_id)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')