from flask import Flask, render_template, redirect, request, Response, make_response
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

app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = {'LFA': []}
auth = auth.Auth()
queue = {}

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
patterns = load_file('patterns.json')
launchers_to_add = load_file('launchers.json')
notes = load_file('notes.json')

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
        notes=json.dumps(notes)
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
    global notes
    notes = note_data
    save_notes()

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
        notes=json.dumps(notes)
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
        if request.form['type'] == 'serial':

            try:
                launcher_mgmt.SerialLauncher(launcher_io, form['launcher_name'], form['serial_port'], int(form['count']))
            except launcher_mgmt.LauncherNotFound:
                return render_template('add_launcher.html', error=True)
            
        elif request.form['type'] == 'shiftregister':

            try:
                launcher_mgmt.ShiftRegisterLauncher(launcher_io, form['launcher_name'], form['serial_port'], int(form['count']))
            except launcher_mgmt.LauncherNotFound:
                return render_template('add_launcher.html', error=True)
        
        else:

            try:
                launcher_mgmt.IPLauncher(launcher_io, form['launcher_name'], form['serial_port'], int(form['count']))
            except launcher_mgmt.LauncherNotFound:
                return render_template('add_launcher.html', error=True)

        fireworks_launched[form['serial_port']] = []
        if not form['serial_port'] in firework_profiling:
            firework_profiling[form['serial_port']] = {'1': {'color': '#177bed', 'fireworks': list(range(1, int(form['count'])+1)), 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale'}}
            save_fp(firework_profiling)
        threading.Thread(target=firework_serial_write, args=[form['serial_port']]).start()
        return redirect('/')
    else:
        return render_template('add_launcher.html', error=False)

@app.route('/patterns')
def patterns_():
    """
    Path that shows the page for viewing and managing
    patterns
    """

    return render_template('patterns/patterns.html', patterns=patterns)

@app.route('/patterns/add', methods=['GET', 'POST'])
def add_pattern():
    """
    Path for the pattern builder.
    """

    if request.method == 'POST':
        pattern_name = request.form['pattern_name']
        pattern_data = json.loads(request.form['pattern_data'])
        patterns[pattern_name] = pattern_data
        f = open('config/patterns.json', 'w')
        f.write(json.dumps(patterns, indent=4))
        f.close()
        return redirect('/patterns')

    launcher_counts = {}
    launchers = {}
    for launcher in launcher_io.launchers:
        launchers[launcher] = launcher_io.launchers[launcher].name
        launcher_counts[launcher] = launcher_io.launchers[launcher].count

    return render_template('patterns/add.html', launcher_counts=json.dumps(launcher_counts), launchers=launchers, firework_profiles=json.dumps(firework_profiling), notes=json.dumps(notes))

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

@socketio.on('run_pattern')
def run_pattern(pattern):
    threading.Thread(target=run_pattern_threaded, args=[pattern]).start()

def run_pattern_threaded(pattern):
    """
    Runs a pattern, this is called from SocketIO,
    /static/js/patterns.js.
    """
    if not pattern in patterns:
        return None
    with app.app_context():
        socketio.send('running_pattern', pattern, broadcast=True)
    pattern_data = patterns[pattern]
    pins_changed = []
    for step in pattern_data:
        pins_changed.append([pattern_data[step]['launcher'], pattern_data[step]['pins']])
    global fireworks_launched
    for pin in pins_changed:
        fireworks_launched[pin[0]].append(pin[1])
        with app.app_context():
            socketio.send('firework_launch', {'firework': pin[1], 'launcher': pin[0]}, broadcast=True)
    launcher_io.run_pattern(pattern_data)
    with app.app_context():
        socketio.send("finished_pattern", pattern, broadcast=True)
    
@socketio.on('delete_pattern')
def delete_pattern(pattern):
    """
    Deletes a pattern, called from the patterns
    js file.
    """

    if not pattern in patterns:
        return None
    del patterns[pattern]
    f = open('config/patterns.json', 'w')
    f.write(json.dumps(patterns))
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
        if launcher_data['type'] == 'serial':
            launcher_mgmt.SerialLauncher(launcher_io, launcher_data['name'], launcher, launcher_data['count'])
        elif launcher_data['type'] == 'ip':
            launcher_mgmt.IPLauncher(launcher_io, launcher_data['name'], launcher, launcher_data['count'])
        elif launcher_data['type'] == 'shiftregister':
            launcher_mgmt.ShiftRegisterLauncher(launcher_io, launcher_data['name'], launcher, launcher_data['count'])
        
        fireworks_launched[launcher] = []
        if not launcher in firework_profiling:
            firework_profiling[launcher] = {'1': {'color': '#177bed', 'fireworks': list(range(1, launcher_data['count']+1)), 'name': 'One Shot'}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot'}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot'}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale'}}
            save_fp(firework_profiling)
        threading.Thread(target=firework_serial_write, args=[launcher]).start()

    socketio.run(app, host='0.0.0.0', port=80)
