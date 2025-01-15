# app.py
import os
from flask_socketio import SocketIO
from flask import Flask, render_template
from shared_memory_dict import SharedMemoryDict

app = Flask(__name__)
sio = SocketIO(app, message_queue='redis://')
smd = SharedMemoryDict(name='msg_in', size=1024)


# bot = get_bot('a!')


@app.route('/')
def index():
    return render_template('index.html')


# runs when a message is received from the socketio server
@sio.on('decrypt_out', namespace='/')
def decrypt_out(data):
    prefix = str(data["input_data"]).split(' ')[0]
    message = str(data["input_data"]).split(' ', 1)[1]
    smd['message'] = (True, prefix, message)

@sio.on('connect_to_bot', namespace='/')
def connect_to_bot(data):
    prefix = str(data["prefix_out"])
    smd['connect'] = (True, prefix)


if __name__ == '__main__':
    sio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), log_output=False,  allow_unsafe_werkzeug=True)
