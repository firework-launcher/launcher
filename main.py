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

@app.route('/')
def home():
    cookies = dict(request.cookies)
    admin = False
    if 'admin' in cookies:
        if cookies['admin'] == 'true':
            admin = True
    serial_ports = []
    old_ports = launcher_io.get_ports()
    for launcher in old_ports:
        serial_ports.append(old_ports[launcher])
    launcher_counts = {}
    for launcher in launcher_io.launchers:
        launcher_counts[launcher] = launcher_io.launchers[launcher].count
    return render_template('home.html', 
        fireworks_launched=json.dumps(fireworks_launched),
        admin=admin,
        firework_profiles=json.dumps(firework_profiling),
        launchers=launcher_io.get_ports(),
        launchers_parsed=':'.join(serial_ports),
        launcher_counts=json.dumps(launcher_counts)
    )

def get_lfa_firework_launched(firework_count):
    lfa_list = []

    for x in range(firework_count):
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
    admin = False
    if 'admin' in cookies:
        if cookies['admin'] == 'true':
            admin = True
    firework_count = 0
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].count > firework_count:
            firework_count = launcher_io.launchers[launcher].count
    return render_template('home.html', 
        fireworks_launched=json.dumps(get_lfa_firework_launched(firework_count)),
        admin=admin,
        firework_profiles=json.dumps({'LFA': {'1': {'color': '#fc2339', 'fireworks': list(range(1, firework_count+1)), 'name': 'LFA'}}}),
        launchers={'Launch For All': 'LFA'},
        launcher_counts=json.dumps({'LFA': firework_count}),
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
    if request.method == 'POST':
        form = dict(request.form)
        if request.form['type'] == 'serial':
            launcher_mgmt.SerialLauncher(launcher_io, form['launcher_name'], form['serial_port'], int(form['count']))
        elif request.form['type'] == 'shiftregister':
            launcher_mgmt.ShiftRegisterLauncher(launcher_io, form['launcher_name'], form['serial_port'], int(form['count']))
        else:
            launcher_mgmt.IPLauncher(launcher_io, form['launcher_name'], form['serial_port'], int(form['count']))
        fireworks_launched[form['serial_port']] = []
        if not form['serial_port'] in firework_profiling:
            firework_profiling[form['serial_port']] = {'1': {'color': '#177bed', 'fireworks': list(range(1, int(form['count'])+1)), 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale'}}
            save_fp(firework_profiling)
        threading.Thread(target=firework_serial_write, args=[form['serial_port']]).start()
        return redirect('/')
    else:
        return render_template('add_launcher.html')

@socketio.on('save_fp')
def save_fp(firework_profiles):
    os.remove('firework_profiles.json')
    f = open('firework_profiles.json', 'x')
    f.write(json.dumps(firework_profiles, indent=4))
    f.close()
    global firework_profiling
    firework_profiling = firework_profiles

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
                launcher_io.write_to_launcher(launcher, '/digital/{}/0\r\n'.format(pin), int(pin)-1)
                launcher_io.write_to_launcher(launcher, '/digital/{}/1\r\n'.format(pin), int(pin)-1)
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
    ports = launcher_io.get_ports()
    launcher = data['launcher']
    if launcher == 'LFA':
        for launcher_ in ports:
            trigger_firework({'launcher': ports[launcher_], 'firework': firework})
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
