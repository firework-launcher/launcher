from flask import Flask, render_template, redirect, request, Response, make_response, jsonify, abort
import string
import threading
import time
import os
import flask_socketio
import sys
import json
import urllib.parse
import launcher_mgmt
import terminal_mgmt
import argparse
import logging
import auth
import subprocess
import socket
import random
import config_mgmt

app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = {'LFA': []}
auth = auth.Auth()
terminals = terminal_mgmt.Terminals()
config = config_mgmt.ConfigMGMT()
queue = {}
sequence_status = {}

config.load_file('firework_profiles.json')
config.load_file('sequences.json')
config.load_file('launchers.json')
config.load_file('notes.json')
config.load_file('branding.json', placeholder_data={'name': 'Firework Launcher'})

update_filename = None

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

launcher_io = launcher_mgmt.LauncherIOMGMT(logging)

@app.route('/')
def home():
    """
    Path / for the webserver.
    """

    launchers_armed = {}
    for launcher in launcher_io.launchers:
        launchers_armed[launcher] = launcher_io.launchers[launcher].armed

    return render_template('home.html', 
        launchers=launcher_io.get_ports(),
        launchers_armed=launchers_armed,
        lfa=False,
        name=config.config['branding']['name']
    )

@app.route('/home/launcher_json_data')
def launcher_json_data():
    launcher_ports = []
    old_ports = launcher_io.get_ports()
    for launcher in old_ports:
        launcher_ports.append(old_ports[launcher])
    root = {
        'fireworks_launched': fireworks_launched,
        'firework_profiles': config.config['firework_profiles'],
        'launchers': launcher_ports,
        'notes': config.config['notes'],
        'sequences': config.config['sequences']
    }

    root['launcher_data'] = {
        'counts': {},
        'names': {},
        'armed': {}
    }
    for launcher in launcher_io.launchers:
        root['launcher_data']['counts'][launcher] = launcher_io.launchers[launcher].count
        root['launcher_data']['names'][launcher] = launcher_io.launchers[launcher].name
        root['launcher_data']['armed'][launcher] = launcher_io.launchers[launcher].armed
    
    return jsonify(root)

def get_lfa_firework_launched(firework_count):
    """
    Used by the /lfa path to get information about which fireworks have
    been launched.
    """

    lfa_list = []

    for x in range(firework_count):
        launched = False
        for launcher in fireworks_launched:
            if x+1 in fireworks_launched[launcher]:
                launched = True
        if launched:
            lfa_list.append(x+1)
    return {'LFA': lfa_list}

@socketio.on("note_update")
def note_update(note_data):
    if not note_data['launcher'] in config.config['notes']:
        config.config['notes'][note_data['launcher']] = {}
    config.config['notes'][note_data['launcher']][str(note_data['firework'])] = note_data['note']
    config.save_config()
    socketio.emit('note_update', note_data)

def check_lfa_armed():
    lfa_armed = False
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].armed:
            lfa_armed = True
    return lfa_armed

@app.route('/lfa')
def lfa():
    """
    Renders the home template, but changes variables are being used.
    When you launch a firework on this page, it will launch that
    same firework on all the launchers.
    """
    
    return render_template('home.html', 
        launchers={'Launch For All': 'LFA'},
        launchers_armed={'LFA': check_lfa_armed()},
        lfa=True,
        name=config.config['branding']['name']
    )

@app.route('/lfa/launcher_json_data')
def lfa_launcher_json_data():
    lfa_armed = check_lfa_armed()
    firework_count = 0
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].count > firework_count:
            firework_count = launcher_io.launchers[launcher].count
    root = {
        'fireworks_launched': get_lfa_firework_launched(firework_count),
        'firework_profiles': {'LFA': {'1': {'color': '#fc2339', 'fireworks': list(range(1, firework_count+1)), 'name': 'LFA'}}},
        'launchers': ['LFA'],
        'notes': config.config['notes'],
        'sequences': config.config['sequences']
    }

    root['launcher_data'] = {
        'counts': {'LFA': firework_count},
        'names': {'LFA': 'Launch For All'},
        'armed': {'LFA': lfa_armed}
    }
    
    return jsonify(root)

@app.route('/settings/terminals')
def terminals_():
    """
    Path for managing terminals.
    """

    return render_template('settings/terminals/terminals.html', terminals=terminals.open_terminal_processes, name=config.config['branding']['name'], page='Terminals')

@app.route('/settings/terminals/add/<string:small_screen>')
def add_terminal(small_screen):
    """
    Generates a random port and creates a terminal session.
    """
    
    if small_screen == 'true':
        small_screen = True
    else:
        small_screen = False
    port = random.randrange(13000, 23000)
    terminals.create_terminal(port, small_screen)
    return redirect('/settings/terminals/sessions/{}'.format(port))

@socketio.on('remove_terminal')
def remove_terminal(port):
    """
    Removes a terminal.
    """

    terminals.delete_terminal(port)

@app.route('/settings/terminals/sessions/<string:port>')
def terminal_client(port):
    """
    Displays a terminal session
    """

    if not port in terminals.open_terminal_processes:
        abort(404)
    
    return render_template('settings/terminals/client.html', url='http://' + socket.gethostbyname(socket.gethostname()) + ':' + port + '/s/local/.', name=config.config['branding']['name'], page='Terminal')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Path for logging in, in the beforerequest function,
    it redirects anyone not logged in to this page.
    """

    if request.method == 'POST':
        if auth.login(request.form['username'], request.form['passwd']):
            token = auth.create_token(request.form['username'], request.remote_addr)
            resp = redirect('/')
            resp.set_cookie('token', token)
            return resp
        else:
            return render_template('login.html', name=config.config['branding']['name'])
    else:
        return render_template('login.html', name=config.config['branding']['name'])

@app.route('/settings/launchers/add', methods=['GET', 'POST'])
def add_launcher():
    """
    Path for adding new launchers. There is a form on the
    settings/launchers/add.html template that is used to
    connect to launchers. It makes a new object for each
    launcher that is used for communicating to that launcher.
    """

    cookies = dict(request.cookies)
    if request.method == 'POST':
        form = dict(request.form)

        try:
            launcher_io.launcher_types[form['type']](launcher_io, form['launcher_name'], form['port'], int(form['count']))
        except launcher_mgmt.LauncherNotFound:
            return render_template('settings/launchers/add.html', error=True, name=config.config['branding']['name'], page='Add Launcher')

        fireworks_launched[form['port']] = []
        if not form['port'] in config.config['firework_profiles']:
            config.config['firework_profiles'][form['port']] = {'1': {'color': '#177bed', 'fireworks': list(range(1, int(form['count'])+1)), 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale'}}
        else:
            for channel in range(1, int(form['count'])+1):
                found = False
                for profile in config.config['firework_profiles'][form['port']]:
                    if channel in config.config['firework_profiles'][form['port']][profile]['fireworks']:
                        found = True
                if not found:
                    for profile in config.config['firework_profiles'][form['port']]:
                        break
                    config.config['firework_profiles'][form['port']][profile]['fireworks'].append(channel)
        config.save_config()
        threading.Thread(target=firework_serial_write, args=[form['port']]).start()
        return redirect('/')
    else:
        return render_template('settings/launchers/add.html', error=False, type_metadata=launcher_io.launcher_type_metadata, name=config.config['branding']['name'], page='Add Launcher')

@app.route('/settings/launchers')
def launcher_settings():
    """
    Path for adding and removing launchers.
    """

    return render_template('settings/launchers/launchers.html', launchers=launcher_io.get_ports(), add_on_start=config.config['launchers'], urlencode=urllib.parse.quote, name=config.config['branding']['name'], page='Launchers')

@app.route('/settings/launchers/edit_fp/<path:launcher>')
def launcher_edit_fp(launcher):
    launcher = launcher[5:]
    if not launcher in launcher_io.launchers:
        abort(404)
    return render_template('settings/launchers/edit_fp.html',
        profilesjson=json.dumps(config.config['firework_profiles'][launcher]),
        profiles=config.config['firework_profiles'][launcher],
        launcher_port=launcher,
        launcher=launcher_io.launchers[launcher].name,
        name=config.config['branding']['name'],
        page='Edit Profiles'
    )

@socketio.on('update_fp')
def update_fp(data):
    launcher = data['launcher']
    profiles = data['profiles']
    config.config['firework_profiles'][launcher] = profiles
    config.save_config()

@socketio.on('launcher_addonstart')
def launcher_addonstart(launcher):
    """
    Adds or removes from the launchers config file.
    """

    if launcher in config.config['launchers']:
        del config.config['launchers'][launcher]
    else:
        config.config['launchers'][launcher] = {
            'name': launcher_io.launchers[launcher].name,
            'type': launcher_io.launchers[launcher].type,
            'count': launcher_io.launchers[launcher].count
        }
    
    config.save_config()

@socketio.on("arm")
def arm(launcher):
    """
    Arms a launcher
    """

    if launcher == 'LFA':
        for launcher in launcher_io.launchers:
            arm(launcher)
        socketio.emit('arm', 'LFA')
    else:
        launcher_io.launchers[launcher].arm()
        socketio.emit('arm', launcher)

@socketio.on("disarm")
def disarm(launcher):
    """
    Disarms a launcher
    """
    
    if launcher == 'LFA':
        for launcher in launcher_io.launchers:
            launcher_io.launchers[launcher].disarm()
            disarm(launcher)
        socketio.emit('disarm', 'LFA')
    else:
        launcher_io.launchers[launcher].disarm()
        socketio.emit('disarm', launcher)

@socketio.on('remove_launcher')
def remove_launcher(launcher):
    """
    Removes a launcher.
    """
    
    launcher_io.launchers[launcher].remove()
    del launcher_io.launchers[launcher]

@app.route('/sequence_status/<string:sequence>')
def sequence_status_checker(sequence):
    if sequence in sequence_status:
        response = {'running': sequence_status[sequence], 'error': False}
        if response['running']:
            response.update(launcher_io.running_sequence_data[sequence])
        if response['error']:
            logging.error('sequence "{}" failed to run'.format(sequence))
            sequence_status[sequence] = False
            return jsonify({'error': 'sequence failed to run'})
        else:
            del response['error']
        
        response['next_step_in'] = launcher_io.running_sequence_data[sequence]['next_step_epoch_est'] - int(time.time())
        return jsonify(response)
    else:
        return jsonify({'running': False})

@app.route('/sequences')
def sequences_():
    """
    Path that shows the page for viewing and managing
    sequences
    """

    return render_template('sequences/sequences.html', sequences=config.config['sequences'], name=config.config['branding']['name'], page='Sequences')

@app.route('/sequences/add', methods=['GET', 'POST'])
def add_sequence():
    """
    Path for the sequence builder.
    """

    if request.method == 'POST':
        sequence_name = request.form['sequence_name']
        sequence_data = json.loads(request.form['sequence_data'])
        config.config['sequences'][sequence_name] = sequence_data
        config.save_config()
        return redirect('/sequences')

    launcher_counts = {}
    launchers = {}
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].sequences_supported:
            launchers[launcher] = launcher_io.launchers[launcher].name
            launcher_counts[launcher] = launcher_io.launchers[launcher].count
    
    if launchers == {}:
        return redirect('/settings/launchers/add')

    return render_template('sequences/add.html', launchers=launchers, name=config.config['branding']['name'], page='Add Sequence')

def secure_filename(filename):
    """
    Replacement for werkzeug.secure_filename()
    since I was having trouble trying to get it
    working. This works fine.
    """

    allowed_characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + '-.'
    new_filename = []
    for x in filename:
        if not x in allowed_characters:
            new_filename.append('_')
        else:
            new_filename.append(x)
    return ''.join(new_filename)

@app.route('/settings')
def settings():
    """
    Settings menu path
    """

    return render_template('settings/settings.html', name=config.config['branding']['name'], page='Settings')

@app.route('/settings/update', methods=['POST'])
def settings_update():
    """
    Saves files uploaded and prepares to update
    using the uploaded file.
    """

    update_file = request.files['update']
    filename = secure_filename(update_file.filename)
    update_file.save(filename)
    global update_filename
    update_filename = filename
    return render_template('settings/update/wait_for_update.html', name=config.config['branding']['name'], page='Updating')

@app.route('/update_ready')
def update_ready():
    """
    The wait for update page makes a request
    here to show that the wait for update page
    is loaded and it can shut down the webserver
    for updating.
    """

    if not update_filename == None:
        subprocess.Popen([sys.executable, 'update.py', update_filename, str(os.getpid())])
    else:
        abort(400)

@app.route('/ping')
def ping():
    """
    Used by the wait for update page to see
    if the webserver is up.
    """

    return 'Pong'

@socketio.on('save_fp')
def save_fp(firework_profiles):
    """
    Writes to the firework_profiles.json file new data
    from the client.
    """

    config.config['firework_profiles'] = firework_profiles
    config.save_config()

@socketio.on('run_sequence')
def run_sequence(sequence):
    """
    Runs a sequence, this is called from SocketIO,
    /static/js/sequences.js.
    """

    socketio.emit('running_sequence', sequence)
    sequence_status[sequence] = True
    threading.Thread(target=run_sequence_threaded, args=[sequence]).start()

def run_sequence_threaded(sequence):
    """
    Thread run_sequence() starts. This is a thread
    because it has delays and interrupts the flask
    app.
    """

    if not sequence in config.config['sequences']:
        return None
    sequence_data = config.config['sequences'][sequence]
    pins_changed = []
    for step in sequence_data:
        pins_changed.append([sequence_data[step]['launcher'], sequence_data[step]['pins']])
    global fireworks_launched
    for pin in pins_changed:
        fireworks_launched[pin[0]] += pin[1]
    launcher_io.run_sequence(sequence, sequence_data)
    if not launcher_io.running_sequence_data[sequence]['error']:
        sequence_status[sequence] = False

@socketio.on('delete_sequence')
def delete_sequence(sequence):
    """
    Deletes a sequence, called from the sequences
    js file.
    """

    if not sequence in config.config['sequences']:
        return None
    del config.config['sequences'][sequence]
    config.save_config()

@socketio.on('delete_note')
def delete_note(note):
    """
    Deletes a note, called from the notes
    js file.
    """

    launcher = note.split('_')[0]
    firework = note.split('_')[1]
    if launcher in config.config['notes']:
        if firework in config.config['notes'][launcher]:
            exists = True
    if not exists:
        return None
    
    del config.config['notes'][launcher][firework]
    config.save_config()
    socketio.emit('delete_note', {
        'launcher': launcher,
        'firework': firework
    })

@socketio.on('stop_sequence')
def stop_sequence(sequence):
    """
    Stops a sequence
    """

    launcher_io.running_sequence_data[sequence]['stop'] = True
    launcher_io.running_sequence_data[sequence]['running'] = False

@app.before_request
def beforerequest():
    """
    Redirects anyone who is not in a private network to
    Rick Astley - Never Gonna Give You Up. This also
    redirects anyone not logged in to the login page
    if they are on a private network.
    """
    if not request.remote_addr.startswith('192.168.') and not request.remote_addr.startswith('172.16.') and not request.remote_addr.startswith('10.'):
        return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    else:
        if not request.path.startswith('/static') and not request.path == '/login':
            if 'token' in request.cookies:
                if auth.verify_token(request.remote_addr, request.cookies['token']) == False:
                    return redirect('/login')
            else:
                return redirect('/login')

            if launcher_io.launchers == {} and not request.path.startswith('/settings'):
                return redirect('/settings/launchers/add')

def firework_serial_write(launcher):
    """
    This is the queue thread. There is a seperate queue for
    each launcher. This way, the LFA page can work well.
    """

    global queue
    queue[launcher] = []
    logging.info('Serial Proccessing Thread Starting for launcher {}...'.format(launcher))
    queue_for_thread = []
    while True:
        try:
            i = 0
            for pin in queue[launcher]:
                launcher_io.write_to_launcher(launcher, int(pin), 0)
                launcher_io.write_to_launcher(launcher, int(pin), 1)
                del queue[launcher][i]
                i = i + 1
                logging.info('{} Queue update: {}'.format(launcher, queue))
        except Exception as e:
            logging.error('Recieved error from queue {}: {}: {}'.format(launcher, type(e).__name__, str(e)))
            queue[launcher] = []
            logging.debug('Due to the previous error, launcher\'s queue was completely cleared')
        time.sleep(0.01)

@socketio.on("launch_firework")
def trigger_firework(data):
    """
    This is ran when a firework is launched using SocketIO
    from /static/js/main.js. It adds to a dictionary that
    the queue thread reads.
    """

    firework = data['firework']
    ports = launcher_io.get_ports()
    launcher = data['launcher']
    if launcher == 'LFA':
        armed = check_lfa_armed()
    else:
        armed = launcher_io.launchers[launcher].armed
    if armed:
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
    """
    This fully clears the queue.
    """
    for launcher in queue:
        queue[launcher] = []

def reset_launcher(launcher):
    """
    This resets a launcher.
    """

    global queue
    global fireworks_launched
    global if_reset

    fireworks_launched[launcher] = []
    reset_queue()

@socketio.on('exec_reset')
def reset(data):
    """
    Function called when a launcher is reset from
    SocketIO.
    """

    if data['launcher'] == 'LFA':
        reset_all()
    else:
        reset_launcher(data['launcher'])
        socketio.emit('reset', data)

@socketio.on('reset_all')
def reset_all():
    """
    Resets all launchers.
    """
    
    for launcher in fireworks_launched:
        reset_launcher(launcher)
    socketio.emit('reset_all')

if __name__ == '__main__':
    for launcher in config.config['launchers']:
        launcher_data = config.config['launchers'][launcher]
        launcher_io.launcher_types[launcher_data['type']](launcher_io, launcher_data['name'], launcher, launcher_data['count'])

        fireworks_launched[launcher] = []
        if not launcher in config.config['firework_profiles']:
            config.config['firework_profiles'][launcher] = {'1': {'color': '#177bed', 'fireworks': list(range(1, launcher_data['count']+1)), 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale'}}
        else:
            for channel in range(1, launcher_data['count']+1):
                found = False
                for profile in config.config['firework_profiles'][launcher]:
                    if channel in config.config['firework_profiles'][launcher][profile]['fireworks']:
                        found = True
                if not found:
                    for profile in config.config['firework_profiles'][launcher]:
                        break
                    config.config['firework_profiles'][launcher][profile]['fireworks'].append(channel)
        config.save_config()
        threading.Thread(target=firework_serial_write, args=[launcher]).start()

    socketio.run(app, host='0.0.0.0', port=80)
