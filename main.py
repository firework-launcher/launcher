from flask import Flask, render_template, redirect, request, Response, make_response, jsonify, abort
import string
import threading
import time
import os
import flask_socketio
import sys
import json
import launcher_mgmt
import argparse
import logging
import auth
import subprocess

app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = {'LFA': []}
auth = auth.Auth()
queue = {}
sequence_status = {}

def load_file(file):
    if not os.path.exists('config/' + file):
        f = open('config/' + file, 'x')
        f.write('{}')
        f.close()
    f = open('config/' + file)
    data = json.loads(f.read())
    f.close()
    return data

if not os.path.exists('config'):
    os.mkdir('config')

firework_profiling = load_file('firework_profiles.json')
sequences = load_file('sequences.json')
launchers_to_add = load_file('launchers.json')
notes = load_file('notes.json')
update_filename = None

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

launcher_io = launcher_mgmt.LauncherIOMGMT(logging)

@app.route('/')
def home():
    """
    Path / for the webserver. It creates lists to pass on to the client,
    and renders the template home.html.
    """

    cookies = dict(request.cookies)
    serial_ports = []
    old_ports = launcher_io.get_ports()
    for launcher in old_ports:
        serial_ports.append(old_ports[launcher])
    launcher_counts = {}
    for launcher in launcher_io.launchers:
        launcher_counts[launcher] = launcher_io.launchers[launcher].count
    launcher_names = {}
    for launcher in launcher_io.launchers:
        launcher_names[launcher] = launcher_io.launchers[launcher].name
    return render_template('home.html', 
        fireworks_launched=json.dumps(fireworks_launched),
        firework_profiles=json.dumps(firework_profiling),
        launchers=launcher_io.get_ports(),
        launchers_parsed=':'.join(serial_ports),
        launcher_counts=json.dumps(launcher_counts),
        launcher_names=json.dumps(launcher_names),
        notes=json.dumps(notes),
        sequences=json.dumps(sequences)
    )

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

def save_notes():
    f = open('config/notes.json', 'w')
    f.write(json.dumps(notes, indent=4))
    f.close()

@socketio.on("note_update")
def note_update(note_data):
    if not note_data['launcher'] in notes:
        notes[note_data['launcher']] = {}
    notes[note_data['launcher']][str(note_data['firework'])] = note_data['note']
    save_notes()
    socketio.emit('note_update', note_data)

@app.route('/lfa')
def lfa():
    """
    Renders the home template, but changes variables are being used.
    When you launch a firework on this page, it will launch that
    same firework on all the launchers.
    """

    cookies = dict(request.cookies)
    firework_count = 0
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].count > firework_count:
            firework_count = launcher_io.launchers[launcher].count
    return render_template('home.html', 
        fireworks_launched=json.dumps(get_lfa_firework_launched(firework_count)),
        firework_profiles=json.dumps({'LFA': {'1': {'color': '#fc2339', 'fireworks': list(range(1, firework_count+1)), 'name': 'LFA'}}}),
        launchers={'Launch For All': 'LFA'},
        launcher_counts=json.dumps({'LFA': firework_count}),
        launchers_parsed='LFA',
        launcher_names=json.dumps({'LFA': 'Launch For All'}),
        notes=json.dumps(notes),
        sequences=json.dumps(sequences)
    )

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
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/add_launcher', methods=['GET', 'POST'])
def add_launcher():
    """
    Path for adding new launchers. There is a form on the
    add_launcher.html template that is used to connect
    to launchers. It makes a new object for each launcher
    that is used for communicating to that launcher.
    """

    cookies = dict(request.cookies)
    if request.method == 'POST':
        form = dict(request.form)

        try:
            launcher_io.launcher_types[form['type']](launcher_io, form['launcher_name'], form['port'], int(form['count']))
        except launcher_mgmt.LauncherNotFound:
            return render_template('add_launcher.html', error=True)

        fireworks_launched[form['port']] = []
        if not form['port'] in firework_profiling:
            firework_profiling[form['port']] = {'1': {'color': '#177bed', 'fireworks': list(range(1, int(form['count'])+1)), 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale'}}
            save_fp(firework_profiling)
        threading.Thread(target=firework_serial_write, args=[form['port']]).start()
        return redirect('/')
    else:
        return render_template('add_launcher.html', error=False, type_metadata=launcher_io.launcher_type_metadata)

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

    return render_template('sequences/sequences.html', sequences=sequences)

@app.route('/sequences/add', methods=['GET', 'POST'])
def add_sequence():
    """
    Path for the sequence builder.
    """

    if request.method == 'POST':
        sequence_name = request.form['sequence_name']
        sequence_data = json.loads(request.form['sequence_data'])
        sequences[sequence_name] = sequence_data
        f = open('config/sequences.json', 'w')
        f.write(json.dumps(sequences, indent=4))
        f.close()
        return redirect('/sequences')

    launcher_counts = {}
    launchers = {}
    for launcher in launcher_io.launchers:
        launchers[launcher] = launcher_io.launchers[launcher].name
        launcher_counts[launcher] = launcher_io.launchers[launcher].count

    return render_template('sequences/add.html', launcher_counts=json.dumps(launcher_counts), launchers=launchers, firework_profiles=json.dumps(firework_profiling), notes=json.dumps(notes))

def secure_filename(filename):
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
    return render_template('settings/settings.html')

@app.route('/settings/update', methods=['POST'])
def settings_update():
    update_file = request.files['update']
    filename = secure_filename(update_file.filename)
    update_file.save(filename)
    global update_filename
    update_filename = filename
    return render_template('settings/update/wait_for_update.html')

@app.route('/update_ready')
def update_ready():
    if not update_filename == None:
        subprocess.Popen([sys.executable, 'update.py', update_filename, str(os.getpid())])
    else:
        abort(400)

@app.route('/ping')
def ping():
    return 'Pong'

@socketio.on('save_fp')
def save_fp(firework_profiles):
    """
    Writes to the firework_profiles.json file new data
    from the client.
    """

    f = open('config/firework_profiles.json', 'w')
    f.write(json.dumps(firework_profiles, indent=4))
    f.close()
    global firework_profiling
    firework_profiling = firework_profiles

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

    if not sequence in sequences:
        return None
    sequence_data = sequences[sequence]
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

    if not sequence in sequences:
        return None
    del sequences[sequence]
    f = open('config/sequences.json', 'w')
    f.write(json.dumps(sequences))
    f.close()

@socketio.on('delete_note')
def delete_note(note):
    """
    Deletes a note, called from the notes
    js file.
    """

    launcher = note.split('_')[0]
    firework = note.split('_')[1]
    if launcher in notes:
        if firework in notes[launcher]:
            exists = True
    if not exists:
        return None
    
    del notes[launcher][firework]
    save_notes()
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

            if launcher_io.launchers == {} and not request.path == '/add_launcher':
                return redirect('/add_launcher')

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
    for launcher in launchers_to_add:
        launcher_data = launchers_to_add[launcher]
        launcher_io.launcher_types[launcher_data['type']](launcher_io, launcher_data['name'], launcher, launcher_data['count'])

        fireworks_launched[launcher] = []
        if not launcher in firework_profiling:
            firework_profiling[launcher] = {'1': {'color': '#177bed', 'fireworks': list(range(1, launcher_data['count']+1)), 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale'}}
            save_fp(firework_profiling)
        threading.Thread(target=firework_serial_write, args=[launcher]).start()

    socketio.run(app, host='0.0.0.0', port=80)
