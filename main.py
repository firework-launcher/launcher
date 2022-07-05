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
devmode = False
if os.path.exists('devmode'):
    devmode = True

if not devmode:
    ser = Serial('/dev/ttyACM0', 115200)
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
    if not request.remote_addr.startswith('192.168.'):
        return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

def firework_serial_write():
    global queue
    global queue_reset_inprogress
    global run_serial_write
    global ready_for_restart
    print('Serial Proccessing Thread Starting...')
    while run_serial_write:
        try:
            i = 0
            for pin in queue:
                if not devmode:
                    ser.write('/digital/{}/0\r\n'.format(pin).encode())
                    data = ser.read()
                    time.sleep(0.5)
                    data_left = ser.inWaiting()
                    data += ser.read(data_left)
                    print(data)
                    time.sleep(0.5)
                    ser.write('/digital/{}/1\r\n'.format(pin).encode())
                    data = ser.read()
                    time.sleep(0.5)
                    data_left = ser.inWaiting()
                    data += ser.read(data_left)
                    print(data)
                del queue[i]
                i = i + 1
                print(queue)
        except:
            pass
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
    socketio.run(app, host='0.0.0.0', port=80)
except RuntimeError as e:
    if str(e) == 'Shutdown':
        sys.exit(0)
