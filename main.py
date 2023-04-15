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
import launcher_mgmt
import argparse
import logging

app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = {'LFA': []}
queue = {}
run_serial_write = True
ready_for_restart = False

if not os.path.exists('firework_profiles.json'):
    f = open('firework_profiles.json', 'x')
    f.write('{}')
    f.close()

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

launcher_io = launcher_mgmt.LauncherIOMGMT(logging)

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
    for launcher in launcher_io.launcher_serial_ports:
        serial_ports.append(launcher_io.launcher_serial_ports[launcher])
    return render_template('home.html', 
        theme=theme,
        fireworks_launched=json.dumps(fireworks_launched),
        admin=admin,
        get_theme_link=get_theme_link,
        firework_profiles=json.dumps(firework_profiling),
        launchers=launcher_io.launcher_serial_ports,
        launchers_parsed=':'.join(serial_ports)
    )

def get_lfa_firework_launched():
    lfa_list = []
    for x in range(32):
        launched = False
        for launcher in fireworks_launched:
            if x+1 in fireworks_launched[launcher]:
                launched = True
        if launched:
            lfa_list.append(x+1)
    return {'LFA': lfa_list}

@app.route('/lfa')
def lfa():
    cookies = dict(request.cookies)
    theme = 'dark'
    if 'theme' in cookies:
        theme = cookies['theme']
    admin = False
    if 'admin' in cookies:
        if cookies['admin'] == 'true':
            admin = True
    return render_template('home.html', 
        theme=theme,
        fireworks_launched=json.dumps(get_lfa_firework_launched()),
        admin=admin,
        get_theme_link=get_theme_link,
        firework_profiles='{"LFA": {"1": {"color": "#fc2339", "fireworks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32], "name": "LFA"}}}',
        launchers={'Launch For All': 'LFA'},
        launchers_parsed='LFA'
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
        if request.form['serialip'] == 'serial':
            launcher_io.add_launcher_serial(form['launcher_name'], form['serial_port'])
        else:
            launcher_io.add_launcher_ip(form['launcher_name'], form['serial_port'])
        fireworks_launched[form['serial_port']] = []
        if not form['serial_port'] in firework_profiling:
            firework_profiling[form['serial_port']] = {'1': {'color': '#177bed', 'fireworks': [7, 8, 9, 10, 11, 13, 16, 17, 12, 2, 3, 6, 15, 4, 14, 5, 1], 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [28, 27, 26, 25, 24], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [23, 22, 21, 20, 19, 18], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [32, 31, 30, 29], 'name': 'Finale'}}
            save_fp(firework_profiling)
        threading.Thread(target=firework_serial_write, args=[form['serial_port']]).start()
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
    f.write(json.dumps(firework_profiles, indent=4))
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

def firework_serial_write(launcher):
    global queue
    global queue_reset_inprogress
    global run_serial_write
    global ready_for_restart
    queue[launcher] = []
    logging.info('Serial Proccessing Thread Starting for launcher {}...'.format(launcher))
    queue_for_thread = []
    while run_serial_write:
        try:
            i = 0
            for pin in queue[launcher]:
                launcher_io.write_to_launcher(launcher, '/digital/{}/0\r\n'.format(pin))
                launcher_io.write_to_launcher(launcher, '/digital/{}/1\r\n'.format(pin))
                del queue[launcher][i]
                i = i + 1
                logging.info('{} Queue update: {}'.format(launcher, queue))
        except Exception as e:
            logging.error('Recieved error from queue {}: {}: {}'.format(launcher, type(e).__name__, str(e)))
            queue[launcher] = []
            logging.debug('Due to the previous error, launcher\'s queue was completely cleared')
        time.sleep(0.01)
    ready_for_restart = True
    print('Serial Processing Thread Exiting...')

@socketio.on("launch_firework")
def trigger_firework(data):
    firework = data['firework']
    launcher = data['launcher']
    if launcher == 'LFA':
        for launcher_ in launcher_io.launcher_serial_ports:
            trigger_firework({'launcher': launcher_io.launcher_serial_ports[launcher_], 'firework': firework})
    else:
        global fireworks_launched
        fireworks_launched[launcher].append(firework)
        pin = str(int(firework)+1)
        global queue
        queue[launcher].append(pin)
    socketio.emit('firework_launch', {'firework': firework, 'launcher': launcher})

def reset_queue():
    for launcher in queue:
        queue[launcher] = []

def reset_launcher(launcher):
    global queue
    global fireworks_launched
    global if_reset

    fireworks_launched[launcher] = []
    reset_queue()

@socketio.on('exec_reset')
def reset(data):
    if data['launcher'] == 'LFA':
        reset_all()
    else:
        reset_launcher(data['launcher'])
        socketio.emit('reset', data)

@socketio.on('reset_all')
def reset_all():
    for launcher in fireworks_launched:
        reset_launcher(launcher)
    socketio.emit('reset_all')

try:
    socketio.run(app, host=args.host, port=args.port)
except RuntimeError as e:
    if str(e) == 'Shutdown':
        sys.exit(0)
