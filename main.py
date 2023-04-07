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
import serial_mgmt
import argparse
import logging

app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = {}
queue = []
run_serial_write = True
ready_for_restart = False
f = open('firework_profiles.json')
firework_profiling = json.loads(f.read())
f.close()

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, help='Host address to host the website with', required=False)
parser.add_argument('--port', type=int, help='Port to bind to for the website', required=False)

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

if args.host == None:
    args.host = '0.0.0.0'

if args.port == None:
    args.port = 80

serial = serial_mgmt.SerialMGMT(logging)

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
    admin = False
    if 'admin' in cookies:
        if cookies['admin'] == 'true':
            admin = True
    serial_ports = []
    for launcher in serial.launcher_serial_ports:
        serial_ports.append(serial.launcher_serial_ports[launcher])
    return render_template('home.html', 
        theme=theme,
        fireworks_launched=json.dumps(fireworks_launched),
        admin=admin,
        get_theme_link=get_theme_link,
        firework_profiles=json.dumps(firework_profiling),
        launchers=serial.launcher_serial_ports,
        launchers_parsed=':'.join(serial_ports)
    )

@app.route('/get_admin')
def admin():
    resp = make_response(redirect('/'))
    resp.set_cookie('admin', 'true')
    return resp

@app.route('/add_launcher', methods=['GET', 'POST'])
def add_launcher():
    cookies = dict(request.cookies)
    theme = 'dark'
    if 'theme' in cookies:
        theme = cookies['theme']
    if request.method == 'POST':
        form = dict(request.form)
        serial.add_launcher(form['launcher_name'], form['serial_port'])
        fireworks_launched[form['serial_port']] = []
        return redirect('/')
    else:
        return render_template('add_launcher.html', get_theme_link=get_theme_link, theme=theme)

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
    logging.info('Serial Proccessing Thread Starting...')
    while run_serial_write:
        try:
            i = 0
            for launcher, pin in queue:
                serial.write_to_launcher(launcher, '/digital/{}/0\r\n'.format(pin))
                serial.write_to_launcher(launcher, '/digital/{}/1\r\n'.format(pin))
                del queue[i]
                i = i + 1
                logging.info('Queue update: {}'.format(queue))
        except Exception as e:
            logging.error('Recieved error from queue: {}: {}'.format(type(e).__name__, str(e)))
            queue = []
            logging.debug('Due to the previous error, queue was completely cleared')
        time.sleep(0.01)
    ready_for_restart = True
    print('Serial Processing Thread Exiting...')

@socketio.on("launch_firework")
def trigger_firework(data):
    firework = data['firework']
    launcher = data['launcher']
    global fireworks_launched
    fireworks_launched[launcher].append(firework)
    pin = str(int(firework)+1)
    global queue
    queue.append((launcher, pin))
    socketio.emit('firework_launch', {'firework': firework, 'launcher': launcher})

@socketio.on('exec_reset')
def reset(data):
    global queue
    global fireworks_launched
    global if_reset
    launcher = data['launcher']
    fireworks_launched[launcher] = []
    queue = []
    socketio.emit('reset', {'launcher': launcher})

threading.Thread(target=firework_serial_write).start()
try:
    socketio.run(app, host=args.host, port=args.port)
except RuntimeError as e:
    if str(e) == 'Shutdown':
        sys.exit(0)
