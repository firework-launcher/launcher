from flask import Flask, render_template, redirect, request, Response, make_response
import uuid
import threading
import time
import os
import flask_socketio
import subprocess
import sys
import requests
import json
from serial import Serial
import argparse
import logging

app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = []
queue = []
run_serial_write = True
amount_of_fireworks = 32
ready_for_restart = False
f = open('firework_profiles.json')
firework_profiling = json.loads(f.read())
f.close()

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, help='Host address to host the website with', required=False)
parser.add_argument('--port', type=int, help='Port to bind to for the website', required=False)
parser.add_argument('serial_port', type=str, help='Serial port to send commands to')

args = parser.parse_args()

if args.serial_port == None:
    args.serial_port = '/dev/ttyACM0'

if args.host == None:
    args.host = '0.0.0.0'

if args.port == None:
    args.port = 80

ser = Serial(args.serial_port, 115200)

def get_theme_link(theme):
    file = None
    if theme == 'light':
        file = 'light.css'
    if theme == 'dark':
        file = 'dark.css'
    return '/static/css/themes/' + file

@app.route('/')
def home():
    cookies = dict(request.cookies)
    theme = 'dark'
    if 'theme' in cookies:
        theme = cookies['theme']
    rows = amount_of_fireworks
    admin = False
    if 'admin' in cookies:
        if cookies['admin'] == 'true':
            admin = True
    fireworks_launched_str = []
    for firework in fireworks_launched:
        fireworks_launched_str.append(str(firework))
    return render_template('home.html', theme=theme, rows=rows, fireworks_launched=':'.join(fireworks_launched_str), admin=admin, get_theme_link=get_theme_link, firework_profiles=json.dumps(firework_profiling))

@app.route('/get_admin')
def admin():
    resp = make_response(redirect('/'))
    resp.set_cookie('admin', 'true')
    return resp

@app.route('/theme/<string:theme>')
def select_theme(theme):
    resp = make_response(redirect('/'))
    resp.set_cookie('theme', theme)
    return resp

@socketio.on('save_fp')
def save_fp(firework_profiles):
    os.remove('firework_profiles.json')
    f = open('firework_profiles.json', 'x')
    f.write(json.dumps(firework_profiles))
    f.close()
    global firework_profiling
    firework_profiling = firework_profiles

@app.route('/themes')
def themes():
    cookies = dict(request.cookies)
    theme = 'dark'
    if 'theme' in cookies:
        theme = cookies['theme']
    return render_template('themes.html', theme=theme, get_theme_link=get_theme_link)

@app.route('/remove_admin')
def remove_admin():
    resp = make_response(redirect('/'))
    resp.set_cookie('admin', 'false')
    return resp

@app.before_request
def rickastley():
    if not request.remote_addr.startswith('192.168.') and not request.remote_addr.startswith('172.16.'):
        return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

def firework_serial_write():
    global queue
    global queue_reset_inprogress
    global run_serial_write
    global ready_for_restart
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    logging.info('Serial Proccessing Thread Starting...')
    while run_serial_write:
        try:
            i = 0
            for pin in queue:
                serial_msg = '/digital/{}/0\r\n'.format(pin)
                ser.write(serial_msg.encode())
                logging.debug('Sent serial message: {} to launcher {}'.format(serial_msg.replace('\r\n', ''), args.serial_port))

                data = ser.read()
                time.sleep(0.5)
                data_left = ser.inWaiting()
                data += ser.read(data_left)
                logging.debug('Recieved serial response: {}'.format(data))
                time.sleep(0.5)

                serial_msg = '/digital/{}/1\r\n'.format(pin)
                ser.write(serial_msg.encode())
                logging.debug('Sent serial message: {} to launcher {}'.format(serial_msg.replace('\r\n', ''), args.serial_port))

                data = ser.read()
                time.sleep(0.5)
                data_left = ser.inWaiting()
                data += ser.read(data_left)
                logging.debug('Recieved serial response: {}'.format(data))
                
                del queue[i]
                i = i + 1
                logging.info('Queue update: {}'.format(queue))
        except:
            pass
        time.sleep(0.01)
    ready_for_restart = True
    print('Serial Processing Thread Exiting...')

@socketio.on("launch_firework")
def trigger_firework(data):
    firework = data['firework']
    global fireworks_launched
    fireworks_launched.append(firework)
    pin = str(int(firework)+1)
    global queue
    queue.append(pin)
    socketio.emit('firework_launch', {'firework': firework})

@socketio.on('exec_reset')
def reset():
    global queue
    global fireworks_launched
    global if_reset
    fireworks_launched = []
    queue = []
    socketio.emit('reset')

threading.Thread(target=firework_serial_write).start()
try:
    socketio.run(app, host=args.host, port=args.port)
except RuntimeError as e:
    if str(e) == 'Shutdown':
        sys.exit(0)
