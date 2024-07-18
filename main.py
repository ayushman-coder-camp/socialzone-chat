from flask import Flask, render_template, redirect, url_for, session, request
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jhjsagdhshdgs'
socketio = SocketIO(app)

chatrooms = {}

def create_room_code(len):
    while True:
        code = ''
        for _ in range(len):
            code = random.choice(ascii_uppercase)
        
        if code not in chatrooms:
            break
    
    return code

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        enter_btn = request.form.get('enter-btn', False)
        create_btn = request.form.get('create-btn', False)

        if not name:
            return render_template('home.html', error='You need to enter a name.', roomcode=code, name=name)
        if enter_btn != False and not code:
            return render_template('home.html', error='You need to enter a code.', roomcode=code, name=name)
        
        chatroom = code
        if create_btn != False:
            chatroom = create_room_code(6)
            chatrooms[chatroom] = { 'people': 0, 'messages': [] }
        elif code not in chatrooms:
            return render_template('home.html', error='Chat room does not exist.', roomcode=code, name=name)
        
        session['chatroom'] = chatroom
        session['name'] = name
        return redirect(url_for('chatroom'))

    return render_template('home.html')

@app.route('/chatroom')
def chatroom():
    chatroom = session.get('chatroom')
    if chatroom is None or session.get('name') is None or chatroom not in chatrooms:
        return redirect(url_for('home'))
    
    return render_template('chat.html', code=chatroom, messages=chatrooms[chatroom]['messages'])

@socketio.on('message')
def message(data):
    chatroom = session.get('chatroom')

    if chatroom not in  chatrooms:
        return
    
    content = {
        'name': session.get('name'),
        'message': data['data']
    }

    send(content, to=chatroom)
    chatrooms[chatroom]['messages'].append(content)


@socketio.on('connect')
def connect(authentication):
    chatroom = session.get('chatroom')
    name = session.get('name')

    if not chatroom or not name:
        return
    
    if chatroom not in chatrooms:
        leave_room(chatroom)
        return
    
    join_room(chatroom)
    send({"name": name, "message": 'entered the room'}, to=chatroom)
    chatrooms[chatroom]['people'] += 1
    print(f'{name} joined room {chatroom}')

@socketio.on('disconnect')
def disconnect():
    chatroom = session.get('chatroom')
    name = session.get('name')
    leave_room(chatroom)

    if chatroom in chatrooms:
        chatrooms[chatroom]['people'] -= 1
        if chatrooms[chatroom]['people'] <= 0:
            del chatrooms[chatroom]
    
    send({"name": name, "message": 'left the room'}, to=chatroom)
    print(f'{name} left room {chatroom}')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=2501)